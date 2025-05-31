"""
AI Monitoring Service

Provides comprehensive monitoring and metrics collection for AI operations
including performance tracking, error monitoring, and usage analytics.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import asyncio
from collections import defaultdict, deque
import aioredis
from ..models import AIMetric
from ..exceptions import MonitoringError
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for monitoring AI operations and collecting metrics."""
    
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.metrics_prefix = "cotai:metrics:"
        self.local_metrics = deque(maxlen=1000)  # Local buffer for metrics
        self.operation_counters = defaultdict(int)
        self.error_counters = defaultdict(int)
        self.performance_history = defaultdict(lambda: deque(maxlen=100))
        
    async def initialize(self) -> None:
        """Initialize monitoring service."""
        try:
            if settings.REDIS_URL:
                self.redis_client = aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self.redis_client.ping()
            logger.info("AI Monitoring service initialized successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed for monitoring: {e}")
            # Continue without Redis - use local storage only
    
    async def close(self) -> None:
        """Close monitoring service connections."""
        if self.redis_client:
            await self.redis_client.close()
      async def record_operation(
        self,
        operation: str,
        success: bool,
        processing_time: float,
        model_used: Optional[str] = None,
        confidence: Optional[float] = None,
        error_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record an AI operation metric."""
        try:
            timestamp = datetime.utcnow()
            metric = AIMetric(
                operation=operation,
                timestamp=timestamp,
                success=success,
                processing_time=processing_time,
                model_used=model_used or settings.OLLAMA_MODEL,
                confidence=confidence,
                error_type=error_type,
                metadata=metadata or {}
            )
            
            # Store in local buffer
            self.local_metrics.append(metric)
            
            # Update counters
            self.operation_counters[operation] += 1
            if not success and error_type:
                self.error_counters[error_type] += 1
            
            # Update performance history
            self.performance_history[operation].append(processing_time)
            
            # Store in Redis if available
            if self.redis_client:
                await self._store_metric_in_redis(metric)
                
            logger.debug(f"Recorded metric for operation: {operation}")
            
        except Exception as e:
            logger.error(f"Failed to record operation metric: {e}")
    
    async def _store_metric_in_redis(self, metric: AIMetric) -> None:
        """Store metric in Redis for persistence."""
        try:
            # Store individual metric
            metric_key = f"{self.metrics_prefix}operation:{metric.operation}:{int(metric.timestamp.timestamp())}"
            metric_data = asdict(metric)
            metric_data['timestamp'] = metric.timestamp.isoformat()
            
            await self.redis_client.hset(
                metric_key,
                mapping=metric_data
            )
            
            # Set expiration (keep metrics for configured days)
            ttl_seconds = settings.AI_METRICS_RETENTION_DAYS * 24 * 3600
            await self.redis_client.expire(metric_key, ttl_seconds)
            
            # Update daily aggregates
            await self._update_daily_aggregates(metric)
            
        except Exception as e:
            logger.warning(f"Failed to store metric in Redis: {e}")
    
    async def _update_daily_aggregates(self, metric: AIMetric) -> None:
        """Update daily aggregate statistics."""
        try:
            date_key = metric.timestamp.strftime("%Y-%m-%d")
            aggregate_key = f"{self.metrics_prefix}daily:{date_key}"
            
            # Update counters and sums
            pipe = self.redis_client.pipeline()
            pipe.hincrby(aggregate_key, f"total_operations", 1)
            pipe.hincrby(aggregate_key, f"op_{metric.operation}", 1)
            
            if metric.success:
                pipe.hincrby(aggregate_key, "successful_operations", 1)
                pipe.hincrbyfloat(aggregate_key, "total_processing_time", metric.processing_time)
            else:
                pipe.hincrby(aggregate_key, "failed_operations", 1)
                if metric.error_type:
                    pipe.hincrby(aggregate_key, f"error_{metric.error_type}", 1)
            
            if metric.confidence is not None:
                pipe.hincrbyfloat(aggregate_key, "total_confidence", metric.confidence)
                pipe.hincrby(aggregate_key, "confidence_count", 1)
            
            # Set expiration for daily aggregates
            ttl_seconds = settings.AI_METRICS_RETENTION_DAYS * 24 * 3600
            pipe.expire(aggregate_key, ttl_seconds)
            
            await pipe.execute()
            
        except Exception as e:
            logger.warning(f"Failed to update daily aggregates: {e}")
      async def get_operation_stats(
        self, 
        operation: Optional[str] = None, 
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get operation statistics for the specified time period."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Filter metrics by time and operation
            filtered_metrics = [
                m for m in self.local_metrics
                if m.timestamp >= cutoff_time and (not operation or m.operation == operation)
            ]
            
            if not filtered_metrics:
                return self._empty_stats()
            
            # Calculate statistics
            total_ops = len(filtered_metrics)
            successful_ops = sum(1 for m in filtered_metrics if m.success)
            failed_ops = total_ops - successful_ops
            
            processing_times = [m.processing_time for m in filtered_metrics if m.processing_time]
            confidences = [m.confidence for m in filtered_metrics if m.confidence is not None]
            
            stats = {
                "total_operations": total_ops,
                "successful_operations": successful_ops,
                "failed_operations": failed_ops,
                "success_rate": (successful_ops / total_ops * 100) if total_ops > 0 else 0,
                "avg_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0,
                "min_processing_time": min(processing_times) if processing_times else 0,
                "max_processing_time": max(processing_times) if processing_times else 0,
                "avg_confidence": sum(confidences) / len(confidences) if confidences else None,
                "error_breakdown": self._get_error_breakdown(filtered_metrics),
                "operation_breakdown": self._get_operation_breakdown(filtered_metrics),
                "time_period_hours": hours
            }
            
            # Add Redis data if available
            if self.redis_client:
                redis_stats = await self._get_redis_stats(operation, hours)
                stats.update(redis_stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get operation stats: {e}")
            return self._empty_stats()
    
    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty stats structure."""
        return {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "success_rate": 0,
            "avg_processing_time": 0,
            "min_processing_time": 0,
            "max_processing_time": 0,
            "avg_confidence": None,
            "error_breakdown": {},
            "operation_breakdown": {},
            "time_period_hours": 0
        }
    
    def _get_error_breakdown(self, metrics: List[AIMetric]) -> Dict[str, int]:
        """Get breakdown of errors by type."""
        error_counts = defaultdict(int)
        for metric in metrics:
            if not metric.success and metric.error_type:
                error_counts[metric.error_type] += 1
        return dict(error_counts)
    
    def _get_operation_breakdown(self, metrics: List[AIMetric]) -> Dict[str, int]:
        """Get breakdown of operations by type."""
        op_counts = defaultdict(int)
        for metric in metrics:
            op_counts[metric.operation] += 1
        return dict(op_counts)
    
    async def _get_redis_stats(self, operation: Optional[str], hours: int) -> Dict[str, Any]:
        """Get additional statistics from Redis."""
        try:
            # Get daily aggregates for the specified period
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=max(1, hours // 24))
            
            total_redis_ops = 0
            total_redis_success = 0
            total_redis_time = 0.0
            
            current_date = start_date
            while current_date <= end_date:
                date_key = current_date.strftime("%Y-%m-%d")
                aggregate_key = f"{self.metrics_prefix}daily:{date_key}"
                
                if await self.redis_client.exists(aggregate_key):
                    daily_data = await self.redis_client.hgetall(aggregate_key)
                    
                    if operation:
                        ops_count = int(daily_data.get(f"op_{operation}", 0))
                    else:
                        ops_count = int(daily_data.get("total_operations", 0))
                    
                    total_redis_ops += ops_count
                    total_redis_success += int(daily_data.get("successful_operations", 0))
                    total_redis_time += float(daily_data.get("total_processing_time", 0))
                
                current_date += timedelta(days=1)
            
            return {
                "redis_total_operations": total_redis_ops,
                "redis_successful_operations": total_redis_success,
                "redis_total_processing_time": total_redis_time
            }
            
        except Exception as e:
            logger.warning(f"Failed to get Redis stats: {e}")
            return {}
    
    async def get_performance_trends(self, operation: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends for an operation."""
        try:
            if operation not in self.performance_history:
                return {"operation": operation, "trend": "no_data", "recent_times": []}
            
            recent_times = list(self.performance_history[operation])
            if len(recent_times) < 2:
                return {"operation": operation, "trend": "insufficient_data", "recent_times": recent_times}
            
            # Calculate trend
            mid_point = len(recent_times) // 2
            first_half_avg = sum(recent_times[:mid_point]) / mid_point
            second_half_avg = sum(recent_times[mid_point:]) / (len(recent_times) - mid_point)
            
            if second_half_avg > first_half_avg * 1.1:
                trend = "degrading"
            elif second_half_avg < first_half_avg * 0.9:
                trend = "improving"
            else:
                trend = "stable"
            
            return {
                "operation": operation,
                "trend": trend,
                "recent_times": recent_times,
                "first_half_avg": first_half_avg,
                "second_half_avg": second_half_avg,
                "change_percentage": ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance trends: {e}")
            return {"operation": operation, "trend": "error", "recent_times": []}
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary of AI operations."""
        try:
            # Get recent stats (last hour)
            recent_stats = await self.get_operation_stats(hours=1)
            
            # Determine health status
            success_rate = recent_stats.get("success_rate", 0)
            avg_time = recent_stats.get("avg_processing_time", 0)
            total_ops = recent_stats.get("total_operations", 0)
            
            if success_rate >= 95 and avg_time < settings.AI_PROCESSING_TIMEOUT * 0.5:
                health_status = "healthy"
            elif success_rate >= 85 and avg_time < settings.AI_PROCESSING_TIMEOUT * 0.8:
                health_status = "warning"
            else:
                health_status = "critical"
            
            # Get active operations
            active_operations = list(self.operation_counters.keys())
            
            # Get most common errors
            top_errors = sorted(
                self.error_counters.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            return {
                "health_status": health_status,
                "success_rate": success_rate,
                "avg_processing_time": avg_time,
                "total_operations_last_hour": total_ops,
                "active_operations": active_operations,
                "top_errors": top_errors,
                "monitoring_active": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get health summary: {e}")
            return {
                "health_status": "unknown",
                "monitoring_active": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def reset_metrics(self, operation: Optional[str] = None) -> bool:
        """Reset metrics for a specific operation or all operations."""
        try:
            if operation:
                # Reset specific operation
                self.operation_counters[operation] = 0
                if operation in self.performance_history:
                    self.performance_history[operation].clear()
                
                # Remove from local metrics
                self.local_metrics = deque(
                    [m for m in self.local_metrics if m.operation != operation],
                    maxlen=1000
                )
            else:
                # Reset all metrics
                self.operation_counters.clear()
                self.error_counters.clear()
                self.performance_history.clear()
                self.local_metrics.clear()
            
            # Clear Redis data if available
            if self.redis_client:
                if operation:
                    pattern = f"{self.metrics_prefix}operation:{operation}:*"
                else:
                    pattern = f"{self.metrics_prefix}*"
                
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            
            logger.info(f"Reset metrics for operation: {operation or 'all'}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset metrics: {e}")
            return False


# Global monitoring service instance
monitoring_service = MonitoringService()

#!/usr/bin/env python3
"""
LLM Integration Test Script

This script tests the LLM integration by performing basic operations
and validating that all services are working correctly.
"""

import asyncio
import sys
import logging
import tempfile
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm import llm_manager
from llm.models import ExtractedTenderData, TenderItem
from llm.exceptions import AIProcessingException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LLMIntegrationTest:
    """Test suite for LLM integration."""
    
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        
        if success:
            self.passed += 1
        else:
            self.failed += 1
    
    async def test_initialization(self) -> bool:
        """Test LLM manager initialization."""
        try:
            await llm_manager.initialize()
            self.log_test("LLM Manager Initialization", True, "Successfully initialized")
            return True
        except Exception as e:
            self.log_test("LLM Manager Initialization", False, f"Failed: {e}")
            return False
    
    async def test_health_check(self) -> bool:
        """Test system health check."""
        try:
            status = await llm_manager.get_system_status()
            healthy = status.get("health", {}).get("healthy", False)
            
            if healthy:
                self.log_test("Health Check", True, "System is healthy")
                return True
            else:
                self.log_test("Health Check", False, f"System unhealthy: {status}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", False, f"Failed: {e}")
            return False
    
    async def test_text_extraction(self) -> bool:
        """Test text extraction with a sample file."""
        try:
            # Create a temporary text file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                test_content = """
TENDER NOTICE
Tender Number: TN-2024-001
Organization: Test Company Ltd
Description: Supply of office equipment
Submission Deadline: 2024-12-31
Estimated Value: $50,000
Requirements:
- Laptops: 10 units
- Printers: 5 units
- Office chairs: 20 units
"""
                temp_file.write(test_content)
                temp_file_path = temp_file.name
            
            try:
                # Test text extraction
                from llm.services.text_extraction import TextExtractionService
                text_service = TextExtractionService()
                extracted_text = await text_service.extract_text(temp_file_path)
                
                if "TN-2024-001" in extracted_text:
                    self.log_test("Text Extraction", True, f"Extracted {len(extracted_text)} characters")
                    return True
                else:
                    self.log_test("Text Extraction", False, "Expected content not found")
                    return False
                    
            finally:
                # Clean up
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.log_test("Text Extraction", False, f"Failed: {e}")
            return False
    
    async def test_tender_data_extraction(self) -> bool:
        """Test tender data extraction with mock data."""
        try:
            # Create a temporary file with tender content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                test_content = """
INVITATION TO TENDER
Tender Reference: ITT-2024-TEST-001
Contracting Authority: Municipal Council
Project Title: Road Maintenance Services
Contract Duration: 12 months
Estimated Contract Value: USD 100,000
Submission Deadline: 15th January 2025, 14:00 hours

SCOPE OF WORK:
1. Pothole repairs - 200 sq meters
2. Road marking - 5 kilometers  
3. Drainage cleaning - 10 manholes

TECHNICAL REQUIREMENTS:
- Minimum 5 years experience in road maintenance
- ISO 9001 certification required
- Equipment: Road roller, asphalt mixer, marking machine

EVALUATION CRITERIA:
- Technical capability: 60%
- Financial proposal: 40%
"""
                temp_file.write(test_content)
                temp_file_path = temp_file.name
            
            try:
                # Test tender data extraction
                result = await llm_manager.extract_tender_data(temp_file_path, use_cache=False)
                
                if result.success and result.data:
                    self.log_test("Tender Data Extraction", True, "Successfully extracted tender data")
                    logger.info(f"Extracted data: {result.data}")
                    return True
                else:
                    self.log_test("Tender Data Extraction", False, f"Extraction failed: {result.error_message}")
                    return False
                    
            finally:
                # Clean up
                os.unlink(temp_file_path)
                
        except Exception as e:
            self.log_test("Tender Data Extraction", False, f"Failed: {e}")
            return False
    
    async def test_quotation_generation(self) -> bool:
        """Test quotation generation with mock tender data."""
        try:
            # Create mock tender data
            tender_data = ExtractedTenderData(
                tender_number="TEST-001",
                organization="Test Municipality",
                title="Road Maintenance Services",
                description="Annual road maintenance contract",
                deadline="2025-01-15",
                estimated_value=100000.0,
                currency="USD",
                items=[
                    TenderItem(
                        description="Pothole repairs",
                        quantity=200,
                        unit="sq meters",
                        specifications=["Asphalt patching", "Quality grade A"]
                    ),
                    TenderItem(
                        description="Road marking",
                        quantity=5,
                        unit="kilometers",
                        specifications=["Thermoplastic paint", "White and yellow lines"]
                    )
                ],
                requirements=["5 years experience", "ISO 9001 certification"],
                evaluation_criteria={"technical": 60, "financial": 40}
            )
            
            # Mock company info
            company_info = {
                "name": "Test Construction Ltd",
                "experience_years": 8,
                "certifications": ["ISO 9001", "ISO 14001"],
                "equipment": ["Road roller", "Asphalt mixer", "Marking machine"],
                "hourly_rate": 75.0,
                "markup_percentage": 15.0
            }
            
            # Test quotation generation
            result = await llm_manager.generate_quotation(
                tender_data=tender_data,
                company_info=company_info,
                use_cache=False
            )
            
            if result.success and result.data:
                self.log_test("Quotation Generation", True, "Successfully generated quotation")
                logger.info(f"Generated quotation: {result.data}")
                return True
            else:
                self.log_test("Quotation Generation", False, f"Generation failed: {result.error_message}")
                return False
                
        except Exception as e:
            self.log_test("Quotation Generation", False, f"Failed: {e}")
            return False
    
    async def test_risk_analysis(self) -> bool:
        """Test risk analysis with mock tender data."""
        try:
            # Create mock tender data with potential risks
            tender_data = ExtractedTenderData(
                tender_number="RISK-TEST-001",
                organization="High Risk Municipality", 
                title="Complex Infrastructure Project",
                description="Multi-year infrastructure development with tight deadlines",
                deadline="2024-12-31",  # Very tight deadline
                estimated_value=10000000.0,  # High value
                currency="USD",
                items=[
                    TenderItem(
                        description="Bridge construction",
                        quantity=1,
                        unit="complete project",
                        specifications=["Seismic resistant", "50 year lifespan", "Environmental compliance"]
                    )
                ],
                requirements=[
                    "Minimum 10 years bridge construction experience",
                    "Environmental impact assessment",
                    "Seismic engineering certification",
                    "Performance bond required"
                ],
                evaluation_criteria={"technical": 70, "financial": 30}
            )
            
            # Test risk analysis
            result = await llm_manager.analyze_risks(tender_data, use_cache=False)
            
            if result.success and result.data:
                self.log_test("Risk Analysis", True, "Successfully analyzed risks")
                logger.info(f"Risk analysis: {result.data}")
                return True
            else:
                self.log_test("Risk Analysis", False, f"Analysis failed: {result.error_message}")
                return False
                
        except Exception as e:
            self.log_test("Risk Analysis", False, f"Failed: {e}")
            return False
    
    async def test_cache_functionality(self) -> bool:
        """Test cache functionality."""
        try:
            from llm.services import cache_service
            
            # Get cache stats
            stats = await cache_service.get_cache_stats()
            self.log_test("Cache Stats", True, f"Cache entries: {stats.get('total_entries', 0)}")
            
            # Test cache clearing
            result = await llm_manager.clear_cache()
            if result.get("success", False):
                self.log_test("Cache Clear", True, f"Cleared {result.get('cleared_entries', 0)} entries")
                return True
            else:
                self.log_test("Cache Clear", False, f"Failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.log_test("Cache Functionality", False, f"Failed: {e}")
            return False
    
    async def test_monitoring(self) -> bool:
        """Test monitoring functionality."""
        try:
            from llm.services import monitoring_service
            
            # Get operation stats
            stats = await monitoring_service.get_operation_stats()
            
            # Get health summary
            health = await monitoring_service.get_health_summary()
            
            if health.get("monitoring_active", False):
                self.log_test("Monitoring", True, f"Health status: {health.get('health_status', 'unknown')}")
                return True
            else:
                self.log_test("Monitoring", False, "Monitoring not active")
                return False
                
        except Exception as e:
            self.log_test("Monitoring", False, f"Failed: {e}")
            return False
    
    async def test_cleanup(self) -> bool:
        """Test cleanup and shutdown."""
        try:
            await llm_manager.close()
            self.log_test("Cleanup", True, "Successfully closed LLM manager")
            return True
        except Exception as e:
            self.log_test("Cleanup", False, f"Failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all integration tests."""
        logger.info("🚀 Starting LLM Integration Tests")
        logger.info("=" * 50)
        
        # Run tests in sequence
        tests = [
            self.test_initialization,
            self.test_health_check,
            self.test_text_extraction,
            self.test_tender_data_extraction,
            self.test_quotation_generation,
            self.test_risk_analysis,
            self.test_cache_functionality,
            self.test_monitoring,
            self.test_cleanup
        ]
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                logger.error(f"Test {test.__name__} crashed: {e}")
                self.log_test(test.__name__, False, f"Test crashed: {e}")
        
        # Print summary
        logger.info("=" * 50)
        logger.info("🏁 Test Summary")
        logger.info(f"Total Tests: {self.passed + self.failed}")
        logger.info(f"Passed: {self.passed}")
        logger.info(f"Failed: {self.failed}")
        logger.info(f"Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        
        if self.failed == 0:
            logger.info("🎉 All tests passed!")
            return True
        else:
            logger.error("❌ Some tests failed:")
            for result in self.test_results:
                if not result["success"]:
                    logger.error(f"  - {result['test']}: {result['message']}")
            return False


async def main():
    """Main test runner."""
    test_suite = LLMIntegrationTest()
    
    try:
        success = await test_suite.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main())

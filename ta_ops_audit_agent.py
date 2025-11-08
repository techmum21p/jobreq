"""
TA Ops Audit Agentic AI System
Automated validation and correction of job requisitions

Architecture:
- Agent 1: Document Extractor - Extracts structured data from PDF
- Agent 2: Validator - Validates against ground truth from SharePoint/Excel
- Agent 3: Corrector - Applies necessary corrections to the document
- Agent 4: Reporter - Updates SharePoint tracker and generates audit reports

Author: Airees (Lead AI Engineer, Philtech Inc.)
Date: November 2025
"""

import anthropic
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import PyPDF2
import openpyxl
from pathlib import Path


class ValidationStatus(Enum):
    """Validation status for each check"""
    PASS = "Yes"
    FAIL = "No"
    FOR_CHECKING = "FOR CHECKING"
    NOT_APPLICABLE = "N/A"


@dataclass
class GroundTruth:
    """Ground truth data from SharePoint tracker"""
    job_requisition_number: str
    business_unit_name: str
    min_pay_rate: float
    max_pay_rate: float
    facility: str
    state: str  # Derived from business unit or location


@dataclass
class ExtractedData:
    """Data extracted from the requisition PDF"""
    job_id: str
    banner: str
    location: str
    state: str
    min_pay_rate: Optional[float]
    max_pay_rate: Optional[float]
    job_schedule: str
    posting_date: str
    role_specific_rates: Dict[str, Tuple[float, float]]
    job_description_present: bool
    pay_transparency_text: str
    has_dollar_signs: bool


@dataclass
class ValidationResult:
    """Result of validation checks"""
    correct_template: ValidationStatus
    correct_min_pay_rate: ValidationStatus
    correct_max_pay_rate: ValidationStatus
    job_description: ValidationStatus
    dollar_sign_included: ValidationStatus
    corrections_needed: List[str]
    corrections_completed: List[str]


class Agent1_DocumentExtractor:
    """
    Agent 1: Document Extractor
    Uses Claude with vision to extract structured data from PDF requisitions
    """
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def extract_from_pdf(self, pdf_path: str) -> ExtractedData:
        """
        Extract structured data from job requisition PDF
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ExtractedData object with all extracted information
        """
        
        # Read PDF and convert to base64 for Claude vision
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text()
        
        # Structured extraction prompt
        extraction_prompt = """
        You are a data extraction specialist for HR job requisitions.
        
        Extract the following information from this job requisition document:
        
        1. Job Identification Number
        2. Banner (e.g., Jewel Osco, Safeway, Vons)
        3. Full Location (address)
        4. US State (extract from location)
        5. Minimum Pay Rate (from page 1, in dollars)
        6. Maximum Pay Rate (from page 1, in dollars)
        7. Job Schedule (Full time/Part time)
        8. Posting Date
        9. Role-specific pay rates (if multiple roles listed with individual ranges)
        10. Check if "Job Description" section exists with standard subsections
        11. Extract the complete "Pay Transparency" section text
        12. Verify if dollar signs ($) are properly formatted in pay rates
        
        CRITICAL RULES:
        - Pay rates must include dollar signs and be formatted as $XX.XX
        - Extract ONLY from the document, do not infer or make up data
        - If a field is not found, mark it as null
        
        Return the data as a JSON object with this exact structure:
        {
            "job_id": "string",
            "banner": "string",
            "location": "string",
            "state": "string (2-letter code)",
            "min_pay_rate": float or null,
            "max_pay_rate": float or null,
            "job_schedule": "string",
            "posting_date": "string",
            "role_specific_rates": {
                "Role Name": [min_rate, max_rate]
            },
            "job_description_present": boolean,
            "pay_transparency_text": "string",
            "has_dollar_signs": boolean
        }
        
        Document text:
        {text}
        """
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": extraction_prompt.format(text=pdf_text)
            }]
        )
        
        # Parse JSON response
        extracted_json = json.loads(response.content[0].text)
        
        return ExtractedData(
            job_id=extracted_json["job_id"],
            banner=extracted_json["banner"],
            location=extracted_json["location"],
            state=extracted_json["state"],
            min_pay_rate=extracted_json["min_pay_rate"],
            max_pay_rate=extracted_json["max_pay_rate"],
            job_schedule=extracted_json["job_schedule"],
            posting_date=extracted_json["posting_date"],
            role_specific_rates=extracted_json["role_specific_rates"],
            job_description_present=extracted_json["job_description_present"],
            pay_transparency_text=extracted_json["pay_transparency_text"],
            has_dollar_signs=extracted_json["has_dollar_signs"]
        )


class Agent2_Validator:
    """
    Agent 2: Validator
    Validates extracted data against ground truth and business rules
    """
    
    def __init__(self, api_key: str, pay_transparency_excel: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        self.pay_transparency_map = self._load_pay_transparency_map(pay_transparency_excel)
    
    def _load_pay_transparency_map(self, excel_path: str) -> Dict[str, str]:
        """Load pay transparency text mapping from Excel"""
        workbook = openpyxl.load_workbook(excel_path)
        sheet = workbook.active
        
        transparency_map = {}
        for row in sheet.iter_rows(min_row=2, values_only=True):
            state = row[0]  # Assuming column A has state codes
            transparency_text = row[1]  # Assuming column B has transparency text
            transparency_map[state] = transparency_text
        
        return transparency_map
    
    def validate(
        self, 
        extracted: ExtractedData, 
        ground_truth: GroundTruth
    ) -> ValidationResult:
        """
        Validate extracted data against ground truth
        
        Args:
            extracted: Data extracted from PDF
            ground_truth: Ground truth from SharePoint tracker
            
        Returns:
            ValidationResult with all validation checks
        """
        corrections_needed = []
        
        # 1. Validate Template (structure check)
        template_valid = ValidationStatus.PASS
        if not extracted.job_description_present:
            template_valid = ValidationStatus.FAIL
            corrections_needed.append("Job description section missing or incomplete")
        
        # 2. Validate Min Pay Rate
        min_rate_valid = ValidationStatus.PASS
        if extracted.min_pay_rate is None:
            min_rate_valid = ValidationStatus.FOR_CHECKING
            corrections_needed.append("Minimum pay rate not found in document")
        elif abs(extracted.min_pay_rate - ground_truth.min_pay_rate) > 0.01:
            min_rate_valid = ValidationStatus.FAIL
            corrections_needed.append(
                f"Min pay rate mismatch: Document shows ${extracted.min_pay_rate:.2f}, "
                f"should be ${ground_truth.min_pay_rate:.2f}"
            )
        
        # 3. Validate Max Pay Rate
        max_rate_valid = ValidationStatus.PASS
        if extracted.max_pay_rate is None:
            max_rate_valid = ValidationStatus.FOR_CHECKING
            corrections_needed.append("Maximum pay rate not found in document")
        elif abs(extracted.max_pay_rate - ground_truth.max_pay_rate) > 0.01:
            max_rate_valid = ValidationStatus.FAIL
            corrections_needed.append(
                f"Max pay rate mismatch: Document shows ${extracted.max_pay_rate:.2f}, "
                f"should be ${ground_truth.max_pay_rate:.2f}"
            )
        
        # 4. Validate Role-Specific Rates (must fall within min-max range)
        for role, (role_min, role_max) in extracted.role_specific_rates.items():
            if role_min < ground_truth.min_pay_rate or role_max > ground_truth.max_pay_rate:
                corrections_needed.append(
                    f"Role '{role}' pay range ${role_min:.2f}-${role_max:.2f} "
                    f"falls outside allowed range ${ground_truth.min_pay_rate:.2f}-"
                    f"${ground_truth.max_pay_rate:.2f}"
                )
        
        # 5. Validate Pay Transparency Text
        expected_transparency = self.pay_transparency_map.get(extracted.state)
        if expected_transparency:
            similarity = self._check_text_similarity(
                extracted.pay_transparency_text,
                expected_transparency
            )
            if similarity < 0.95:  # 95% similarity threshold
                corrections_needed.append(
                    f"Pay transparency text for state {extracted.state} does not match expected template"
                )
        
        # 6. Validate Dollar Sign Formatting
        dollar_sign_valid = ValidationStatus.PASS
        if not extracted.has_dollar_signs:
            dollar_sign_valid = ValidationStatus.FAIL
            corrections_needed.append("Pay rates missing dollar sign ($) formatting")
        
        # 7. Validate Job Description
        job_desc_valid = ValidationStatus.PASS if extracted.job_description_present else ValidationStatus.FAIL
        
        return ValidationResult(
            correct_template=template_valid,
            correct_min_pay_rate=min_rate_valid,
            correct_max_pay_rate=max_rate_valid,
            job_description=job_desc_valid,
            dollar_sign_included=dollar_sign_valid,
            corrections_needed=corrections_needed,
            corrections_completed=[]
        )
    
    def _check_text_similarity(self, text1: str, text2: str) -> float:
        """
        Use LLM to check semantic similarity between two texts
        Returns similarity score between 0 and 1
        """
        prompt = f"""
        Compare these two pay transparency texts and return a similarity score between 0 and 1.
        
        Score 1.0 means they convey the exact same information (even if wording differs slightly).
        Score 0.0 means completely different content.
        
        Text 1:
        {text1}
        
        Text 2:
        {text2}
        
        Return ONLY a single number between 0 and 1, nothing else.
        """
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            return float(response.content[0].text.strip())
        except:
            return 0.0


class Agent3_Corrector:
    """
    Agent 3: Corrector
    Automatically applies corrections to the PDF document
    Uses Claude to generate corrected document content
    """
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def apply_corrections(
        self,
        pdf_path: str,
        extracted: ExtractedData,
        ground_truth: GroundTruth,
        validation_result: ValidationResult,
        pay_transparency_map: Dict[str, str]
    ) -> Tuple[str, List[str]]:
        """
        Apply corrections to the document
        
        Args:
            pdf_path: Original PDF path
            extracted: Extracted data
            ground_truth: Ground truth data
            validation_result: Validation results
            pay_transparency_map: State to pay transparency text mapping
            
        Returns:
            Tuple of (corrected_document_path, list_of_corrections_applied)
        """
        
        if not validation_result.corrections_needed:
            return pdf_path, ["No corrections needed"]
        
        # Read original PDF
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            original_text = ""
            for page in pdf_reader.pages:
                original_text += page.extract_text()
        
        # Build correction instructions
        correction_instructions = self._build_correction_instructions(
            extracted, ground_truth, validation_result, pay_transparency_map
        )
        
        # Use Claude to generate corrected document
        correction_prompt = f"""
        You are a document correction specialist for HR job requisitions.
        
        Original document:
        {original_text}
        
        Corrections to apply:
        {correction_instructions}
        
        Generate the CORRECTED version of the entire document with all corrections applied.
        Maintain the exact same format and structure, only change the specific items that need correction.
        
        Return the corrected document text in full.
        """
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8000,
            messages=[{"role": "user", "content": correction_prompt}]
        )
        
        corrected_text = response.content[0].text
        
        # Save corrected document
        corrected_path = pdf_path.replace('.pdf', '_CORRECTED.txt')
        with open(corrected_path, 'w', encoding='utf-8') as f:
            f.write(corrected_text)
        
        corrections_applied = validation_result.corrections_needed.copy()
        
        return corrected_path, corrections_applied
    
    def _build_correction_instructions(
        self,
        extracted: ExtractedData,
        ground_truth: GroundTruth,
        validation_result: ValidationResult,
        pay_transparency_map: Dict[str, str]
    ) -> str:
        """Build detailed correction instructions for the LLM"""
        
        instructions = []
        
        for correction in validation_result.corrections_needed:
            if "Min pay rate mismatch" in correction:
                instructions.append(
                    f"CORRECTION 1: Change 'Minimum Pay Rate' from "
                    f"${extracted.min_pay_rate:.2f} to ${ground_truth.min_pay_rate:.2f}"
                )
            
            elif "Max pay rate mismatch" in correction:
                instructions.append(
                    f"CORRECTION 2: Change 'Maximum Pay Rate' from "
                    f"${extracted.max_pay_rate:.2f} to ${ground_truth.max_pay_rate:.2f}"
                )
            
            elif "Pay transparency text" in correction:
                correct_transparency = pay_transparency_map.get(extracted.state)
                instructions.append(
                    f"CORRECTION 3: Replace the 'Pay Transparency' section with:\n"
                    f"{correct_transparency}"
                )
            
            elif "dollar sign" in correction:
                instructions.append(
                    f"CORRECTION 4: Ensure all pay rates are formatted with dollar signs "
                    f"in the format $XX.XX"
                )
            
            elif "Role" in correction and "pay range" in correction:
                instructions.append(
                    f"CORRECTION 5: {correction} - Adjust role-specific pay ranges to fall "
                    f"within ${ground_truth.min_pay_rate:.2f}-${ground_truth.max_pay_rate:.2f}"
                )
        
        return "\n".join(instructions)


class Agent4_Reporter:
    """
    Agent 4: Reporter
    Updates SharePoint tracker and generates audit reports
    """
    
    def __init__(self, sharepoint_list_url: str):
        self.sharepoint_url = sharepoint_list_url
    
    def update_sharepoint(
        self,
        job_req_number: str,
        validation_result: ValidationResult
    ) -> bool:
        """
        Update SharePoint tracker with validation results
        
        Args:
            job_req_number: Job requisition number
            validation_result: Validation results to update
            
        Returns:
            Success status
        """
        
        # This would use SharePoint REST API or Microsoft Graph API
        # Placeholder for actual implementation
        
        update_data = {
            "Job_Requisition_Number": job_req_number,
            "Correct_Template": validation_result.correct_template.value,
            "Correct_Min_Pay_Rate": validation_result.correct_min_pay_rate.value,
            "Correct_Max_Pay_Rate": validation_result.correct_max_pay_rate.value,
            "Job_Description": validation_result.job_description.value,
            "Dollar_Sign_Included": validation_result.dollar_sign_included.value,
            "Corrections_Completed": len(validation_result.corrections_completed) > 0,
            "Action_Needed": len(validation_result.corrections_needed) > 0
        }
        
        print(f"[SharePoint Update] Job {job_req_number}:")
        print(json.dumps(update_data, indent=2))
        
        # TODO: Implement actual SharePoint API call
        # response = requests.post(self.sharepoint_url, json=update_data, headers=auth_headers)
        
        return True
    
    def generate_audit_report(
        self,
        job_req_number: str,
        extracted: ExtractedData,
        ground_truth: GroundTruth,
        validation_result: ValidationResult,
        corrections_applied: List[str]
    ) -> str:
        """Generate comprehensive audit report"""
        
        report = f"""
========================================
TA OPS AUDIT REPORT
========================================
Job Requisition Number: {job_req_number}
Generated: {Path(__file__).stem}
Date: November 7, 2025

GROUND TRUTH (from SharePoint):
--------------------------------
Business Unit: {ground_truth.business_unit_name}
Min Pay Rate: ${ground_truth.min_pay_rate:.2f}
Max Pay Rate: ${ground_truth.max_pay_rate:.2f}
Facility: {ground_truth.facility}

EXTRACTED DATA (from PDF):
---------------------------
Job ID: {extracted.job_id}
Banner: {extracted.banner}
Location: {extracted.location}
State: {extracted.state}
Min Pay Rate: ${extracted.min_pay_rate:.2f} if extracted.min_pay_rate else "NOT FOUND"
Max Pay Rate: ${extracted.max_pay_rate:.2f} if extracted.max_pay_rate else "NOT FOUND"
Job Description Present: {"Yes" if extracted.job_description_present else "No"}
Dollar Signs Formatted: {"Yes" if extracted.has_dollar_signs else "No"}

VALIDATION RESULTS:
-------------------
✓ Correct Template: {validation_result.correct_template.value}
✓ Correct Min Pay Rate: {validation_result.correct_min_pay_rate.value}
✓ Correct Max Pay Rate: {validation_result.correct_max_pay_rate.value}
✓ Job Description: {validation_result.job_description.value}
✓ Dollar Sign Included: {validation_result.dollar_sign_included.value}

CORRECTIONS NEEDED ({len(validation_result.corrections_needed)}):
-------------------
"""
        for i, correction in enumerate(validation_result.corrections_needed, 1):
            report += f"{i}. {correction}\n"
        
        report += f"""
CORRECTIONS APPLIED ({len(corrections_applied)}):
--------------------
"""
        for i, correction in enumerate(corrections_applied, 1):
            report += f"{i}. {correction}\n"
        
        report += "\n========================================\n"
        
        return report


class TAOpsAuditOrchestrator:
    """
    Main orchestrator that coordinates all agents
    """
    
    def __init__(
        self,
        anthropic_api_key: str,
        pay_transparency_excel: str,
        sharepoint_url: str
    ):
        self.extractor = Agent1_DocumentExtractor(anthropic_api_key)
        self.validator = Agent2_Validator(anthropic_api_key, pay_transparency_excel)
        self.corrector = Agent3_Corrector(anthropic_api_key)
        self.reporter = Agent4_Reporter(sharepoint_url)
    
    def process_requisition(
        self,
        pdf_path: str,
        ground_truth: GroundTruth,
        auto_correct: bool = True
    ) -> Dict:
        """
        Complete end-to-end processing of a job requisition
        
        Args:
            pdf_path: Path to requisition PDF
            ground_truth: Ground truth data from SharePoint
            auto_correct: Whether to automatically apply corrections
            
        Returns:
            Dictionary with processing results
        """
        
        print(f"\n{'='*60}")
        print(f"Processing Job Requisition: {ground_truth.job_requisition_number}")
        print(f"{'='*60}\n")
        
        # Step 1: Extract data from PDF
        print("[Agent 1] Extracting data from PDF...")
        extracted = self.extractor.extract_from_pdf(pdf_path)
        print(f"✓ Extracted data for Job ID: {extracted.job_id}")
        
        # Step 2: Validate against ground truth
        print("\n[Agent 2] Validating against ground truth...")
        validation_result = self.validator.validate(extracted, ground_truth)
        print(f"✓ Validation complete: {len(validation_result.corrections_needed)} issues found")
        
        # Step 3: Apply corrections (if enabled)
        corrected_path = None
        corrections_applied = []
        
        if auto_correct and validation_result.corrections_needed:
            print("\n[Agent 3] Applying corrections...")
            corrected_path, corrections_applied = self.corrector.apply_corrections(
                pdf_path,
                extracted,
                ground_truth,
                validation_result,
                self.validator.pay_transparency_map
            )
            validation_result.corrections_completed = corrections_applied
            print(f"✓ Corrections applied: {len(corrections_applied)} corrections made")
            print(f"✓ Corrected document saved: {corrected_path}")
        
        # Step 4: Update SharePoint and generate report
        print("\n[Agent 4] Updating SharePoint and generating report...")
        self.reporter.update_sharepoint(
            ground_truth.job_requisition_number,
            validation_result
        )
        
        report = self.reporter.generate_audit_report(
            ground_truth.job_requisition_number,
            extracted,
            ground_truth,
            validation_result,
            corrections_applied
        )
        
        # Save report
        report_path = pdf_path.replace('.pdf', '_AUDIT_REPORT.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✓ Audit report saved: {report_path}")
        print(f"✓ SharePoint updated")
        
        print(f"\n{'='*60}")
        print(f"Processing Complete!")
        print(f"{'='*60}\n")
        
        return {
            "job_requisition_number": ground_truth.job_requisition_number,
            "extracted_data": extracted,
            "validation_result": validation_result,
            "corrected_document": corrected_path,
            "audit_report": report_path,
            "corrections_applied": corrections_applied
        }
    
    def batch_process(
        self,
        sharepoint_data: List[GroundTruth],
        pdf_directory: str,
        auto_correct: bool = True
    ) -> List[Dict]:
        """
        Batch process multiple requisitions
        
        Args:
            sharepoint_data: List of ground truth data from SharePoint
            pdf_directory: Directory containing PDF files
            auto_correct: Whether to automatically apply corrections
            
        Returns:
            List of processing results
        """
        
        results = []
        pdf_dir = Path(pdf_directory)
        
        for ground_truth in sharepoint_data:
            # Find matching PDF file
            pdf_file = pdf_dir / f"{ground_truth.job_requisition_number}.pdf"
            
            if not pdf_file.exists():
                print(f"⚠ Warning: PDF not found for job {ground_truth.job_requisition_number}")
                continue
            
            try:
                result = self.process_requisition(
                    str(pdf_file),
                    ground_truth,
                    auto_correct
                )
                results.append(result)
            except Exception as e:
                print(f"✗ Error processing {ground_truth.job_requisition_number}: {str(e)}")
                continue
        
        return results


# Example usage
if __name__ == "__main__":
    
    # Initialize orchestrator
    orchestrator = TAOpsAuditOrchestrator(
        anthropic_api_key="your-api-key-here",
        pay_transparency_excel="/path/to/pay_transparency_by_state.xlsx",
        sharepoint_url="https://your-sharepoint-site.com/api/lists/TAOpsAudit"
    )
    
    # Example ground truth data
    ground_truth = GroundTruth(
        job_requisition_number="651640",
        business_unit_name="27R-Seattle",
        min_pay_rate=14.75,
        max_pay_rate=15.00,
        facility="1148",
        state="IL"
    )
    
    # Process single requisition
    result = orchestrator.process_requisition(
        pdf_path="/path/to/651640.pdf",
        ground_truth=ground_truth,
        auto_correct=True
    )
    
    print("\n" + "="*60)
    print("PROCESSING SUMMARY")
    print("="*60)
    print(f"Job: {result['job_requisition_number']}")
    print(f"Issues Found: {len(result['validation_result'].corrections_needed)}")
    print(f"Corrections Applied: {len(result['corrections_applied'])}")
    print(f"Audit Report: {result['audit_report']}")
    if result['corrected_document']:
        print(f"Corrected Document: {result['corrected_document']}")

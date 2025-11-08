"""
Generate Incorrect Requisition Format for Testing
Creates a PDF with intentional validation errors to test the TA Ops Audit system
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors

def create_incorrect_requisition():
    """
    Create an incorrect job requisition with multiple validation errors:
    
    INTENTIONAL ERRORS:
    1. Wrong Min Pay Rate: $12.50 (should be $14.75)
    2. Wrong Max Pay Rate: $18.00 (should be $15.00)
    3. Missing dollar signs in some rates (16.00 instead of $16.00)
    4. Role-specific rate exceeds max (Meat Associate: $13.50 - $19.00)
    5. Wrong Pay Transparency text (missing Illinois-specific language)
    6. Job Description section incomplete (missing "Why you will choose us")
    7. Inconsistent formatting
    """
    
    # Create PDF
    doc = SimpleDocTemplate(
        "/mnt/user-data/outputs/Incorrect_Requisition_Format.pdf",
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#003087'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#003087'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    subsection_style = ParagraphStyle(
        'Subsection',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    # Header
    elements.append(Paragraph("Albertsons Companies", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Job Title
    elements.append(Paragraph("Retail Sales and Store Support", title_style))
    elements.append(Paragraph("Downers Grove, IL, United States", subtitle_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # JOB INFO Section
    elements.append(Paragraph("JOB INFO", section_style))
    
    job_info_data = [
        ['Job Identification', '651640'],
        ['Job Category', 'Retail, Store Ops'],
        ['Posting Date', '11/04/2025, 11:58 PM'],
        ['Job Schedule', 'Part time'],
        ['Locations', '1148 OGDEN AVE, DOWNERS GROVE, IL, 60515, US'],
        ['Banner', 'Jewel Osco'],
        ['<b>Minimum Pay Rate</b>', '<b>12.50</b>'],  # ERROR 1: Wrong rate & missing $
        ['<b>Maximum Pay Rate</b>', '<b>18.00</b>'],  # ERROR 2: Wrong rate & missing $
    ]
    
    job_info_table = Table(job_info_data, colWidths=[2.5*inch, 4*inch])
    job_info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(job_info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # JOB DESCRIPTION Section
    elements.append(Paragraph("JOB DESCRIPTION", section_style))
    
    # A Day in the Life
    elements.append(Paragraph("A Day in the Life:", subsection_style))
    elements.append(Paragraph(
        "Our sales and store support teams, also known as clerks in the grocery world, "
        "play an important part in ensuring our stores are clean, organized, and shoppable "
        "so that our customers can find exactly what they need to keep their families healthy "
        "and fed. In this role, you are the face of the company and whether you are replenishing "
        "shelves, arranging flowers, preparing produce, or receiving freight, you will always "
        "have the opportunity to interact with our valued customers.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.15*inch))
    
    # What you bring to the table
    elements.append(Paragraph("What you bring to the table:", subsection_style))
    elements.append(Paragraph("• You take pride in the work you do, whether big or small.", styles['Normal']))
    elements.append(Paragraph("• You agree that food is central to all our lives.", styles['Normal']))
    elements.append(Paragraph("• Helping customers and fellow associates gives you energy.", styles['Normal']))
    elements.append(Paragraph("• Smiling and making others smile is your favorite.", styles['Normal']))
    elements.append(Spacer(1, 0.15*inch))
    
    # ERROR 3: Missing "Why you will choose us" section - intentionally omitted
    
    # Starting hourly rates section
    elements.append(Paragraph("Starting hourly rates:", subsection_style))
    elements.append(Paragraph(
        "Starting hourly rates will be no less than the local minimum wage and will vary "
        "based on things like location, experience, qualifications, and the terms of any "
        "applicable collective bargaining agreement.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.1*inch))
    
    # ERROR 4: Role rates - some missing $ and one exceeds max
    elements.append(Paragraph("• Meat Associate - 13.50 - 19.00", styles['Normal']))  # ERROR: Exceeds max & missing $
    elements.append(Paragraph("• Floral Associate - $13.75 – $14.00", styles['Normal']))
    elements.append(Paragraph("• Produce Associate - 13.75 – 14.00", styles['Normal']))  # ERROR: Missing $
    elements.append(Paragraph("• General Merchandise Associate - $13.75 – $14.00", styles['Normal']))
    elements.append(Paragraph("• Receiving/Freight Associate - $13.75 – $14.00", styles['Normal']))
    elements.append(Paragraph("• Grocery Associate - $13.75 – $14.00", styles['Normal']))
    elements.append(Paragraph("• Bakery Associate - $13.75 – $14.00", styles['Normal']))
    
    # Page break
    elements.append(PageBreak())
    
    # ABOUT US Section
    elements.append(Paragraph("ABOUT US", section_style))
    elements.append(Paragraph(
        "Albertsons Companies is at the forefront of the revolution in retail. Committed to "
        "innovation and fostering a culture of belonging, our team is united with a unique "
        "purpose: to bring people together around the joys of food and to inspire well-being. "
        "We want talented individuals to be part of this journey!",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.15*inch))
    
    elements.append(Paragraph(
        "Locally great and nationally strong, Albertsons Companies (NYSE: ACI) is a leading "
        "food and drug retailer in the U.S. We operate over 2,200 stores, 1,732 pharmacies, "
        "405 fuel centers, 22 distribution facilities, and 19 manufacturing plants across 34 "
        "states and the District of Columbia.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.15*inch))
    
    elements.append(Paragraph(
        "Our well-known banners include Albertsons, Safeway, Vons, Jewel-Osco, ACME, Shaw's, "
        "Tom Thumb, United Supermarkets, United Express, Randalls, Albertson's Market, Pavilions, "
        "Star Markets, Market Street, Carrs, Haggen, Lucky, Amigos, Andronico's Community Markets, "
        "King's, Balducci's, and Albertson's Market Street.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.3*inch))
    
    # ERROR 5: Wrong Pay Transparency text (generic instead of Illinois-specific)
    elements.append(Paragraph("Pay Transparency:", subsection_style))
    elements.append(Paragraph(
        "Starting rates will be no less than the local minimum wage and may vary based on "
        "things like location and experience. This position offers competitive compensation.",  # ERROR: Generic text
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.15*inch))
    
    # Disclaimer
    elements.append(Paragraph("Disclaimer", subsection_style))
    elements.append(Paragraph(
        "The above statements are intended to describe the general nature of work performed by "
        "the employees assigned to this job and are not the official job description for the position. "
        "All employees must comply with Company, Division, and Store policies and applicable laws.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.15*inch))
    
    # Equal Opportunity Statement
    elements.append(Paragraph("Albertsons is an Equal Opportunity Employer", subsection_style))
    elements.append(Paragraph(
        "This Company is an Equal Opportunity Employer, and does not discriminate on the basis "
        "of race, gender, ethnicity, religion, national origin, age, disability, veteran status, "
        "gender identity/expression, sexual orientation, or on any other basis prohibited by law.",
        styles['Normal']
    ))
    
    # Build PDF
    doc.build(elements)
    
    return "/mnt/user-data/outputs/Incorrect_Requisition_Format.pdf"


def create_validation_errors_summary():
    """Create a summary document of all intentional errors"""
    
    summary = """
INCORRECT REQUISITION FORMAT - VALIDATION ERRORS SUMMARY
========================================================

This document contains INTENTIONAL ERRORS for testing the TA Ops Audit system.

Job Requisition: 651640
Location: Downers Grove, IL
Position: Retail Sales and Store Support

GROUND TRUTH (Correct Values):
-------------------------------
Minimum Pay Rate: $14.75
Maximum Pay Rate: $15.00
State: Illinois
All rates should have dollar signs ($)
Role-specific rates must fall within $14.75 - $15.00


INTENTIONAL ERRORS IN THIS DOCUMENT:
=====================================

ERROR 1: INCORRECT MINIMUM PAY RATE
------------------------------------
Found: 12.50 (also missing dollar sign)
Should be: $14.75
Location: Job Info section, page 1
Severity: CRITICAL
Expected System Response: Flag as "Correct Min Pay Rate: No"

ERROR 2: INCORRECT MAXIMUM PAY RATE
------------------------------------
Found: 18.00 (also missing dollar sign)
Should be: $15.00
Location: Job Info section, page 1
Severity: CRITICAL
Expected System Response: Flag as "Correct Max Pay Rate: No"

ERROR 3: MISSING DOLLAR SIGNS
------------------------------
Found: Multiple rates without $ symbol
  - Min rate: "12.50" instead of "$12.50"
  - Max rate: "18.00" instead of "$18.00"
  - Meat Associate: "13.50 - 19.00" instead of "$13.50 - $19.00"
  - Produce Associate: "13.75 – 14.00" instead of "$13.75 – $14.00"
Location: Throughout document
Severity: HIGH
Expected System Response: Flag as "Dollar Sign Included: No"

ERROR 4: ROLE-SPECIFIC RATE EXCEEDS MAXIMUM
--------------------------------------------
Found: Meat Associate - 13.50 - 19.00
Issue: Maximum rate of $19.00 exceeds allowed max of $15.00
Should be: $13.50 - $15.00 (or within range)
Location: Starting hourly rates section, page 1
Severity: CRITICAL
Expected System Response: Flag in validation report

ERROR 5: MISSING JOB DESCRIPTION SECTION
-----------------------------------------
Found: "Why you will choose us" section is completely missing
Should have: Complete section with benefits and company culture
Location: Job Description section
Severity: HIGH
Expected System Response: Flag as "Job Description: No" or "FOR CHECKING"

ERROR 6: INCORRECT PAY TRANSPARENCY TEXT
-----------------------------------------
Found: Generic transparency text without Illinois-specific language
Should have: Illinois-specific pay transparency statement with proper legal language
Location: Page 2, Pay Transparency section
Severity: HIGH
Expected System Response: Flag in validation report

ERROR 7: INCOMPLETE TEMPLATE
-----------------------------
Found: Missing standard benefits section
Should have: Complete "Why you will choose us" with benefits list
Location: Job Description section
Severity: MEDIUM
Expected System Response: Flag as "Correct Template: No"


EXPECTED VALIDATION RESULTS:
=============================

SharePoint Tracker Updates:
├── Correct Template: No (missing section)
├── Correct Min Pay Rate: No ($12.50 vs $14.75)
├── Correct Max Pay Rate: No ($18.00 vs $15.00)
├── Job Description: No (incomplete)
├── Dollar Sign Included: No (multiple instances)
└── Action Needed: Yes

Corrections Needed Count: 7 major issues

Processing Time: ~45-60 seconds
Expected Corrected Output: 
  - All pay rates corrected to $14.75 - $15.00
  - Dollar signs added throughout
  - Illinois pay transparency text inserted
  - "Why you will choose us" section added
  - Meat Associate rate adjusted to $13.50 - $15.00


TESTING CHECKLIST:
==================

Agent 1 (Extractor) Should:
□ Extract incorrect min rate: 12.50
□ Extract incorrect max rate: 18.00
□ Identify missing dollar signs
□ Extract role-specific rates
□ Note incomplete job description
□ Extract generic pay transparency text

Agent 2 (Validator) Should:
□ Flag min rate discrepancy
□ Flag max rate discrepancy
□ Flag missing dollar signs
□ Flag role rate exceeding maximum
□ Flag incomplete template
□ Flag incorrect pay transparency text
□ Generate list of 7 corrections needed

Agent 3 (Corrector) Should:
□ Correct min rate to $14.75
□ Correct max rate to $15.00
□ Add dollar signs throughout
□ Adjust Meat Associate rate to max $15.00
□ Add missing "Why you will choose us" section
□ Replace with Illinois-specific transparency text
□ Generate corrected DOCX file

Agent 4 (Reporter) Should:
□ Update SharePoint with all validation results
□ Generate detailed audit report
□ List all 7 corrections applied
□ Create complete audit trail


TEST SUCCESS CRITERIA:
======================

✓ System detects all 7 intentional errors
✓ Validation flags match expected results
✓ Corrected document has all issues fixed
✓ SharePoint updated correctly
✓ Audit report documents all changes
✓ Processing completes without crashes
✓ Output files generated successfully


USE THIS FILE TO:
=================

1. Test the complete TA Ops Audit workflow
2. Verify all 4 agents are working correctly
3. Validate SharePoint integration
4. Ensure correction logic is sound
5. Test error handling and logging
6. Benchmark processing time
7. Generate sample audit reports
8. Demo system capabilities to stakeholders
9. Train team on what errors look like
10. Validate against production data


NEXT STEPS:
===========

1. Run system with this file:
   python config_and_setup.py single \\
     --pdf Incorrect_Requisition_Format.pdf \\
     --job-id 651640

2. Review generated outputs:
   - 651640_CORRECTED.docx
   - 651640_AUDIT_REPORT.txt
   - SharePoint updates

3. Verify all 7 errors were caught and corrected

4. Compare with Correct_Requisition_Format.pdf to validate

"""
    
    with open('/mnt/user-data/outputs/Incorrect_Requisition_ERRORS.txt', 'w') as f:
        f.write(summary)
    
    print("✓ Created error summary: Incorrect_Requisition_ERRORS.txt")


if __name__ == "__main__":
    print("Creating Incorrect Requisition Format for Testing...")
    print("=" * 60)
    print()
    
    # Create the incorrect PDF
    pdf_path = create_incorrect_requisition()
    print(f"✓ Created: {pdf_path}")
    print()
    
    # Create the errors summary
    create_validation_errors_summary()
    print()
    
    print("=" * 60)
    print("INTENTIONAL ERRORS INCLUDED:")
    print("=" * 60)
    print()
    print("1. ❌ Wrong Min Pay Rate: 12.50 (should be $14.75)")
    print("2. ❌ Wrong Max Pay Rate: 18.00 (should be $15.00)")
    print("3. ❌ Missing dollar signs throughout")
    print("4. ❌ Meat Associate rate exceeds max ($19.00 > $15.00)")
    print("5. ❌ Missing 'Why you will choose us' section")
    print("6. ❌ Wrong Pay Transparency text (generic, not IL-specific)")
    print("7. ❌ Incomplete template structure")
    print()
    print("=" * 60)
    print("Expected Validation Results:")
    print("=" * 60)
    print("  Correct Template: No")
    print("  Correct Min Pay Rate: No")
    print("  Correct Max Pay Rate: No")
    print("  Job Description: No")
    print("  Dollar Sign Included: No")
    print("  Corrections Needed: 7")
    print()
    print("=" * 60)
    print("Use this file to test your TA Ops Audit system!")
    print("See Incorrect_Requisition_ERRORS.txt for complete details.")
    print("=" * 60)

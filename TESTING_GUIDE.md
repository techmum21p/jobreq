# 🧪 Testing Guide: Correct vs Incorrect Requisitions

## Overview

I've created two requisition documents for comprehensive testing of your TA Ops Audit system:

1. **Correct_Requisition_Format.pdf** (Uploaded by you - baseline)
2. **Incorrect_Requisition_Format.pdf** (Generated - test validation)

---

## 📊 Side-by-Side Comparison

### Job Details (Same in Both)
- **Job ID**: 651640
- **Position**: Retail Sales and Store Support
- **Location**: 1148 OGDEN AVE, DOWNERS GROVE, IL, 60515
- **Banner**: Jewel Osco
- **State**: Illinois

---

## ❌ 7 Intentional Errors in Incorrect Version

### Error 1: Wrong Minimum Pay Rate
| Aspect | Correct Version | Incorrect Version | Severity |
|--------|----------------|-------------------|----------|
| **Value** | $14.75 | 12.50 | CRITICAL |
| **Formatting** | ✓ Has $ sign | ✗ Missing $ | HIGH |
| **Expected Flag** | - | "Correct Min Pay Rate: No" | - |

### Error 2: Wrong Maximum Pay Rate
| Aspect | Correct Version | Incorrect Version | Severity |
|--------|----------------|-------------------|----------|
| **Value** | $15.00 | 18.00 | CRITICAL |
| **Formatting** | ✓ Has $ sign | ✗ Missing $ | HIGH |
| **Expected Flag** | - | "Correct Max Pay Rate: No" | - |

### Error 3: Missing Dollar Signs
| Location | Correct Version | Incorrect Version |
|----------|----------------|-------------------|
| Min Rate | $14.75 | 12.50 |
| Max Rate | $15.00 | 18.00 |
| Meat Associate | $13.50 - $16.55 | 13.50 - 19.00 |
| Produce Associate | $13.75 - $14.00 | 13.75 – 14.00 |

**Expected Flag**: "Dollar Sign Included: No"

### Error 4: Role Rate Exceeds Maximum
| Role | Correct Version | Incorrect Version | Issue |
|------|----------------|-------------------|-------|
| Meat Associate | $13.50 - $16.55 | 13.50 - 19.00 | Max $19.00 > $15.00 limit |
| Status | ⚠️ Already exceeds | ⚠️ Even worse | Should be ≤ $15.00 |

**Expected Flag**: Validation warning about role rate exceeding limit

### Error 5: Missing Job Description Section
| Section | Correct Version | Incorrect Version |
|---------|----------------|-------------------|
| "A Day in the Life" | ✓ Present | ✓ Present |
| "What you bring to the table" | ✓ Present | ✓ Present |
| "Why you will choose us" | ✓ Present | ✗ **MISSING** |

**Expected Flag**: "Job Description: No" or "Correct Template: No"

### Error 6: Wrong Pay Transparency Text
| Aspect | Correct Version | Incorrect Version |
|--------|----------------|-------------------|
| **Text** | Illinois-specific legal language | Generic text |
| **Content** | Mentions state requirements | No state-specific language |
| **Length** | ~200 words | ~30 words |

**Correct Text Should Include**:
- "Starting rates will be no less than the local minimum wage..."
- State-specific requirements
- Benefits details (medical, dental, 401k, etc.)
- "This is an entry level position with advancement opportunity"
- "Applications are accepted on an on-going basis"

**Incorrect Text** (too generic):
> "Starting rates will be no less than the local minimum wage and may vary based on things like location and experience. This position offers competitive compensation."

**Expected Flag**: Pay transparency validation failure

### Error 7: Incomplete Template Structure
| Element | Correct Version | Incorrect Version |
|---------|----------------|-------------------|
| Job Info section | ✓ Complete | ✓ Complete |
| Job Description | ✓ All subsections | ✗ Missing subsection |
| About Us | ✓ Complete | ✓ Complete |
| Pay Transparency | ✓ Complete | ✗ Incomplete |

**Expected Flag**: "Correct Template: No"

---

## 🧪 Testing Workflow

### Step 1: Test with Correct Version (Baseline)
```bash
python config_and_setup.py single \
  --pdf Correct_Requisition_Format.pdf \
  --job-id 651640
```

**Expected Results**:
```
✓ Correct Template: Yes
⚠️ Correct Min Pay Rate: Yes
⚠️ Correct Max Pay Rate: Yes
✓ Job Description: Yes
✓ Dollar Sign Included: Yes
⚠️ Corrections Needed: 1 (Meat Associate rate adjustment)
```

Note: The correct version already has Meat Associate at $13.50-$16.55 which exceeds $15.00 max, so one correction should be flagged.

### Step 2: Test with Incorrect Version (Full Validation)
```bash
python config_and_setup.py single \
  --pdf Incorrect_Requisition_Format.pdf \
  --job-id 651640
```

**Expected Results**:
```
✗ Correct Template: No
✗ Correct Min Pay Rate: No
✗ Correct Max Pay Rate: No
✗ Job Description: No
✗ Dollar Sign Included: No
✗ Corrections Needed: 7
```

### Step 3: Compare Outputs

**Correct Version Output**:
- Minimal corrections needed
- Mostly passes validation
- Only role rate adjustment needed

**Incorrect Version Output**:
- Multiple critical errors
- Comprehensive corrections needed
- Tests all validation logic

---

## 📋 Validation Checklist

### Agent 1: Document Extractor
Test that it extracts:

**From Correct Version**:
- [x] Min Rate: $14.75
- [x] Max Rate: $15.00
- [x] All role rates with $ signs
- [x] Complete job description
- [x] Full pay transparency text

**From Incorrect Version**:
- [x] Min Rate: 12.50 (no $)
- [x] Max Rate: 18.00 (no $)
- [x] Mixed formatting (some with $, some without)
- [x] Incomplete job description
- [x] Abbreviated pay transparency

### Agent 2: Validator
Test that it flags:

**Correct Version**:
- [x] Meat Associate rate exceeds max (only issue)

**Incorrect Version**:
- [x] Min rate incorrect ($12.50 vs $14.75)
- [x] Max rate incorrect ($18.00 vs $15.00)
- [x] Missing dollar signs (multiple)
- [x] Role rate exceeds max ($19.00 > $15.00)
- [x] Missing template section
- [x] Wrong pay transparency text
- [x] Incomplete structure

### Agent 3: Corrector
Test that it corrects:

**Correct Version**:
- [x] Adjusts Meat Associate to $13.50-$15.00

**Incorrect Version**:
- [x] Changes min rate to $14.75
- [x] Changes max rate to $15.00
- [x] Adds $ signs throughout
- [x] Adjusts Meat Associate to $13.50-$15.00
- [x] Adds missing "Why you will choose us"
- [x] Replaces with Illinois pay transparency text
- [x] Generates properly formatted DOCX

### Agent 4: Reporter
Test that it reports:

**Correct Version**:
- [x] Mostly passing validation
- [x] 1 correction applied
- [x] SharePoint updated

**Incorrect Version**:
- [x] Multiple failures
- [x] 7 corrections applied
- [x] Detailed audit report
- [x] SharePoint updated with all flags

---

## 🎯 Success Criteria

### For Correct Version
```
Processing Time: 30-45 seconds
Validation Accuracy: >95%
Corrections Applied: 1
SharePoint Status: Mostly "Yes", 1 correction flag
Audit Report: Shows minor adjustment needed
```

### For Incorrect Version
```
Processing Time: 45-60 seconds
Validation Accuracy: 100% (catches all 7 errors)
Corrections Applied: 7
SharePoint Status: Multiple "No" flags
Audit Report: Comprehensive list of all issues and fixes
```

---

## 📊 Expected Audit Reports

### Correct Version Report Summary
```
========================================
TA OPS AUDIT REPORT
========================================
Job Requisition Number: 651640

VALIDATION RESULTS:
✓ Correct Template: Yes
✓ Correct Min Pay Rate: Yes
✓ Correct Max Pay Rate: Yes
✓ Job Description: Yes
✓ Dollar Sign Included: Yes

CORRECTIONS NEEDED (1):
1. Meat Associate pay range ($13.50-$16.55) exceeds 
   maximum allowed rate of $15.00

CORRECTIONS APPLIED (1):
1. Adjusted Meat Associate rate to $13.50-$15.00
========================================
```

### Incorrect Version Report Summary
```
========================================
TA OPS AUDIT REPORT
========================================
Job Requisition Number: 651640

VALIDATION RESULTS:
✗ Correct Template: No
✗ Correct Min Pay Rate: No
✗ Correct Max Pay Rate: No
✗ Job Description: No
✗ Dollar Sign Included: No

CORRECTIONS NEEDED (7):
1. Min pay rate: $12.50 → $14.75
2. Max pay rate: $18.00 → $15.00
3. Add dollar signs throughout
4. Meat Associate rate: $19.00 → $15.00
5. Add "Why you will choose us" section
6. Replace pay transparency text with IL version
7. Complete template structure

CORRECTIONS APPLIED (7):
1. Corrected minimum pay rate to $14.75
2. Corrected maximum pay rate to $15.00
3. Added dollar signs to all pay rates
4. Adjusted Meat Associate rate to $13.50-$15.00
5. Inserted complete "Why you will choose us" section
6. Replaced with Illinois-specific transparency text
7. Completed template with all required sections
========================================
```

---

## 🔍 Testing Scenarios

### Scenario 1: Basic Validation
**Input**: Correct_Requisition_Format.pdf
**Expected**: Pass with 1 minor correction
**Tests**: Basic extraction and validation

### Scenario 2: Comprehensive Validation
**Input**: Incorrect_Requisition_Format.pdf
**Expected**: Fail with 7 corrections
**Tests**: All validation rules and correction logic

### Scenario 3: Batch Processing
**Input**: Both files
**Expected**: Process both, different results
**Tests**: Batch handling and result differentiation

### Scenario 4: SharePoint Integration
**Input**: Both files
**Expected**: Different SharePoint updates
**Tests**: Update logic and field mapping

### Scenario 5: Correction Generation
**Input**: Incorrect_Requisition_Format.pdf
**Expected**: Properly formatted corrected DOCX
**Tests**: Document generation and formatting

---

## 🐛 Debugging Guide

### If System Misses Errors

**Check Agent 2 (Validator) Logic**:
```python
# In ta_ops_audit_agent.py
# Add debug logging to see what's being compared
print(f"Extracted min rate: {extracted.min_pay_rate}")
print(f"Ground truth min rate: {ground_truth.min_pay_rate}")
print(f"Difference: {abs(extracted.min_pay_rate - ground_truth.min_pay_rate)}")
```

**Verify Extraction**:
```python
# Check if Agent 1 extracted correctly
extracted = extractor.extract_from_pdf("Incorrect_Requisition_Format.pdf")
print(f"Extracted data: {extracted}")
```

**Test Validation Thresholds**:
```python
# Check tolerance settings in config
pay_rate_tolerance = 0.01  # ±$0.01
# Ensure errors > tolerance are caught
```

### If Corrections Don't Apply

**Check Agent 3 (Corrector) Logic**:
```python
# Verify correction instructions
print(f"Corrections needed: {validation_result.corrections_needed}")
print(f"Applying: {correction_instructions}")
```

**Test Document Generation**:
```python
# Generate test document
corrector.generate_corrected_document(...)
# Open and verify manually
```

---

## 📈 Performance Benchmarks

### Target Metrics

| Metric | Correct Version | Incorrect Version |
|--------|----------------|-------------------|
| Processing Time | 30-45 sec | 45-60 sec |
| Errors Detected | 1 | 7 |
| Corrections Applied | 1 | 7 |
| API Calls | ~3-4 | ~5-6 |
| API Cost | ~$0.15 | ~$0.25 |
| Accuracy | >95% | 100% |

---

## 🎓 Training Use Cases

### For TA Ops Team
1. Show what errors look like
2. Demonstrate validation logic
3. Explain correction process
4. Review audit reports

### For QA Team
1. Verify system accuracy
2. Test edge cases
3. Validate corrections
4. Ensure compliance

### For Stakeholders
1. Demo time savings
2. Show error detection
3. Prove ROI
4. Build confidence

---

## 📝 Test Results Log

```
Date: _______________
Tester: _______________

Test 1: Correct Requisition
[ ] Extracted correctly
[ ] Validated accurately
[ ] 1 correction applied
[ ] SharePoint updated
[ ] Audit report generated
Result: PASS / FAIL

Test 2: Incorrect Requisition  
[ ] Extracted all errors
[ ] Flagged all 7 issues
[ ] Applied all corrections
[ ] SharePoint updated correctly
[ ] Comprehensive audit report
Result: PASS / FAIL

Test 3: Batch Processing
[ ] Both files processed
[ ] Different results recorded
[ ] No crashes or errors
[ ] All outputs generated
Result: PASS / FAIL

Notes:
_________________________________
_________________________________
_________________________________
```

---

## 🚀 Next Steps After Testing

1. **If tests pass**: Deploy to production
2. **If tests fail**: Review logs and debug
3. **Document results**: Share with stakeholders
4. **Iterate**: Improve based on findings
5. **Scale up**: Process larger batches

---

**Created**: November 7, 2025  
**Purpose**: Comprehensive testing of TA Ops Audit system  
**Files**: Correct_Requisition_Format.pdf + Incorrect_Requisition_Format.pdf  
**Expected Outcome**: System catches all 7 intentional errors and applies corrections

---

*Use these test files to validate your system before production deployment!* ✅

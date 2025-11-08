"""
Configuration and Setup Guide for TA Ops Audit Agent System
"""

import os
from pathlib import Path
from typing import Dict
import yaml


class TAOpsConfig:
    """
    Configuration management for TA Ops Audit System
    """
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "config.yaml"
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from YAML file"""
        
        default_config = {
            # API Configuration
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY', ''),
            'claude_model': 'claude-sonnet-4-20250514',
            
            # File Paths
            'paths': {
                'pdf_directory': '/path/to/requisition/pdfs',
                'output_directory': '/path/to/corrected/documents',
                'reports_directory': '/path/to/audit/reports',
                'pay_transparency_excel': '/path/to/pay_transparency_by_state.xlsx',
                'sharepoint_export': '/path/to/sharepoint_export.xlsx'
            },
            
            # SharePoint Configuration
            'sharepoint': {
                'site_url': 'https://rxsafeway.sharepoint.com/sites/ACI.TAOps',
                'list_name': 'TA Ops Audit Report',
                'auth_type': 'oauth',  # or 'certificate'
                'client_id': os.getenv('SHAREPOINT_CLIENT_ID', ''),
                'client_secret': os.getenv('SHAREPOINT_CLIENT_SECRET', ''),
            },
            
            # Processing Configuration
            'processing': {
                'auto_correct': True,
                'batch_size': 10,
                'parallel_processing': False,
                'validation_threshold': 0.95,  # 95% similarity for pay transparency
                'pay_rate_tolerance': 0.01,  # $0.01 tolerance for pay rates
            },
            
            # Notification Configuration
            'notifications': {
                'enabled': True,
                'email_on_completion': True,
                'email_on_errors': True,
                'recipients': ['ta-ops@philtech.com'],
                'slack_webhook': os.getenv('SLACK_WEBHOOK_URL', '')
            },
            
            # Logging Configuration
            'logging': {
                'level': 'INFO',
                'log_file': 'ta_ops_audit.log',
                'log_to_console': True,
                'log_to_file': True
            }
        }
        
        if Path(self.config_path).exists():
            with open(self.config_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
                default_config.update(loaded_config)
        
        return default_config
    
    def save_config(self):
        """Save current configuration to YAML file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, default)
            if value is None:
                return default
        return value


# SharePoint Integration Module
class SharePointIntegration:
    """
    Integration with SharePoint to read ground truth and update results
    """
    
    def __init__(self, config: TAOpsConfig):
        self.config = config
        self.site_url = config.get('sharepoint.site_url')
        self.list_name = config.get('sharepoint.list_name')
    
    def authenticate(self):
        """
        Authenticate with SharePoint
        Can use either OAuth or certificate-based auth
        """
        from office365.sharepoint.client_context import ClientContext
        from office365.runtime.auth.client_credential import ClientCredential
        
        client_id = self.config.get('sharepoint.client_id')
        client_secret = self.config.get('sharepoint.client_secret')
        
        credentials = ClientCredential(client_id, client_secret)
        ctx = ClientContext(self.site_url).with_credentials(credentials)
        
        return ctx
    
    def read_ground_truth(self) -> list:
        """
        Read ground truth data from SharePoint list
        
        Returns:
            List of GroundTruth objects
        """
        from ta_ops_audit_agent import GroundTruth
        
        ctx = self.authenticate()
        list_obj = ctx.web.lists.get_by_title(self.list_name)
        items = list_obj.items.get().execute_query()
        
        ground_truths = []
        for item in items:
            gt = GroundTruth(
                job_requisition_number=item.properties['Job_Requisition_Number'],
                business_unit_name=item.properties['Business_Unit_Name'],
                min_pay_rate=float(item.properties['Min_Pay_rate'].replace('$', '')),
                max_pay_rate=float(item.properties['Max_Pay_Rate'].replace('$', '')),
                facility=item.properties['FACILITY'],
                state=self._extract_state_from_business_unit(
                    item.properties['Business_Unit_Name']
                )
            )
            ground_truths.append(gt)
        
        return ground_truths
    
    def update_validation_results(self, job_req_number: str, results: Dict):
        """
        Update SharePoint list with validation results
        """
        ctx = self.authenticate()
        list_obj = ctx.web.lists.get_by_title(self.list_name)
        
        # Find the item
        items = list_obj.items.filter(
            f"Job_Requisition_Number eq '{job_req_number}'"
        ).get().execute_query()
        
        if len(items) > 0:
            item = items[0]
            item.set_property('Correct_Template', results['correct_template'])
            item.set_property('Correct_Min_Pay_Rate', results['correct_min_pay_rate'])
            item.set_property('Correct_Max_Pay_Rate', results['correct_max_pay_rate'])
            item.set_property('Job_Description', results['job_description'])
            item.set_property('Dollar_Sign_Included', results['dollar_sign_included'])
            item.set_property('Corrections_Completed', results['corrections_completed'])
            item.update()
            ctx.execute_query()
    
    def _extract_state_from_business_unit(self, business_unit: str) -> str:
        """
        Extract state from business unit name
        e.g., '27R-Seattle' -> 'WA'
        """
        # This would need a mapping table or logic
        state_mapping = {
            'Seattle': 'WA',
            'SoCal': 'CA',
            'NorCal': 'CA',
            'Denver': 'CO',
            'Portland': 'OR',
            # ... add more mappings
        }
        
        for key, state in state_mapping.items():
            if key in business_unit:
                return state
        
        return 'Unknown'


# Pay Transparency Loader
class PayTransparencyLoader:
    """
    Load and manage pay transparency text by state
    """
    
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.transparency_map = self._load_map()
    
    def _load_map(self) -> Dict[str, str]:
        """Load pay transparency mapping from Excel"""
        import openpyxl
        
        workbook = openpyxl.load_workbook(self.excel_path)
        sheet = workbook.active
        
        mapping = {}
        
        # Assuming structure:
        # Column A: State Code (e.g., 'CA', 'WA', 'IL')
        # Column B: Pay Transparency Text
        
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if row[0] and row[1]:  # Both state and text exist
                state = str(row[0]).strip().upper()
                transparency_text = str(row[1]).strip()
                mapping[state] = transparency_text
        
        return mapping
    
    def get_transparency_text(self, state: str) -> str:
        """Get pay transparency text for a given state"""
        return self.transparency_map.get(state.upper(), self._get_default_text())
    
    def _get_default_text(self) -> str:
        """Default pay transparency text if state-specific not found"""
        return """
Starting rates will be no less than the local minimum wage and may vary based on 
things like location, experience, qualifications, and the terms of any applicable 
collective bargaining agreement. Dependent on length of service, hours worked and 
any applicable collective bargaining agreement, benefits may include medical, dental, 
vision, disability and life insurance, sick pay, PTO/Vacation pay and retirement 
benefits (pension and/or 401(k) eligibility. This is an entry level position with 
advancement opportunity. Applications are accepted on an on-going basis.
"""


# Complete Setup Example
def setup_ta_ops_system():
    """
    Complete setup and initialization of the TA Ops Audit System
    """
    
    print("="*70)
    print("TA OPS AUDIT SYSTEM - SETUP")
    print("="*70)
    print()
    
    # Step 1: Load configuration
    print("[1/5] Loading configuration...")
    config = TAOpsConfig('config.yaml')
    print("✓ Configuration loaded")
    print()
    
    # Step 2: Verify API key
    print("[2/5] Verifying Anthropic API key...")
    api_key = config.get('anthropic_api_key')
    if not api_key:
        print("⚠ Warning: ANTHROPIC_API_KEY not set!")
        print("   Please set it in config.yaml or as environment variable")
        return None
    print("✓ API key found")
    print()
    
    # Step 3: Initialize SharePoint integration
    print("[3/5] Initializing SharePoint integration...")
    sharepoint = SharePointIntegration(config)
    print("✓ SharePoint integration ready")
    print()
    
    # Step 4: Load pay transparency data
    print("[4/5] Loading pay transparency data...")
    transparency_path = config.get('paths.pay_transparency_excel')
    if not Path(transparency_path).exists():
        print(f"⚠ Warning: Pay transparency file not found: {transparency_path}")
        print("   Please update the path in config.yaml")
        return None
    
    pay_transparency = PayTransparencyLoader(transparency_path)
    print(f"✓ Loaded transparency text for {len(pay_transparency.transparency_map)} states")
    print()
    
    # Step 5: Initialize main orchestrator
    print("[5/5] Initializing TA Ops Audit Orchestrator...")
    from ta_ops_audit_agent import TAOpsAuditOrchestrator
    
    orchestrator = TAOpsAuditOrchestrator(
        anthropic_api_key=api_key,
        pay_transparency_excel=transparency_path,
        sharepoint_url=config.get('sharepoint.site_url')
    )
    print("✓ Orchestrator initialized")
    print()
    
    print("="*70)
    print("SETUP COMPLETE!")
    print("="*70)
    print()
    print("System is ready to process job requisitions.")
    print("Available commands:")
    print("  - orchestrator.process_requisition(pdf_path, ground_truth)")
    print("  - orchestrator.batch_process(sharepoint_data, pdf_directory)")
    print()
    
    return {
        'config': config,
        'orchestrator': orchestrator,
        'sharepoint': sharepoint,
        'pay_transparency': pay_transparency
    }


# Command-line interface
def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='TA Ops Audit Agent - Automated Requisition Validation and Correction'
    )
    
    parser.add_argument(
        'mode',
        choices=['single', 'batch', 'setup'],
        help='Processing mode'
    )
    
    parser.add_argument(
        '--pdf',
        help='Path to PDF file (for single mode)'
    )
    
    parser.add_argument(
        '--job-id',
        help='Job requisition number (for single mode)'
    )
    
    parser.add_argument(
        '--pdf-dir',
        help='Directory containing PDF files (for batch mode)'
    )
    
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--no-correct',
        action='store_true',
        help='Validate only, do not apply corrections'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'setup':
        system = setup_ta_ops_system()
        return
    
    # Initialize system
    config = TAOpsConfig(args.config)
    
    from ta_ops_audit_agent import TAOpsAuditOrchestrator, GroundTruth
    
    orchestrator = TAOpsAuditOrchestrator(
        anthropic_api_key=config.get('anthropic_api_key'),
        pay_transparency_excel=config.get('paths.pay_transparency_excel'),
        sharepoint_url=config.get('sharepoint.site_url')
    )
    
    if args.mode == 'single':
        if not args.pdf or not args.job_id:
            print("Error: --pdf and --job-id required for single mode")
            return
        
        # Load ground truth from SharePoint
        sharepoint = SharePointIntegration(config)
        ground_truths = sharepoint.read_ground_truth()
        
        gt = next(
            (g for g in ground_truths if g.job_requisition_number == args.job_id),
            None
        )
        
        if not gt:
            print(f"Error: Job {args.job_id} not found in SharePoint")
            return
        
        result = orchestrator.process_requisition(
            pdf_path=args.pdf,
            ground_truth=gt,
            auto_correct=not args.no_correct
        )
        
        print("\n" + "="*70)
        print("PROCESSING COMPLETE")
        print("="*70)
        print(f"Job: {result['job_requisition_number']}")
        print(f"Issues: {len(result['validation_result'].corrections_needed)}")
        print(f"Corrections: {len(result['corrections_applied'])}")
        
    elif args.mode == 'batch':
        if not args.pdf_dir:
            print("Error: --pdf-dir required for batch mode")
            return
        
        # Load ground truth from SharePoint
        sharepoint = SharePointIntegration(config)
        ground_truths = sharepoint.read_ground_truth()
        
        results = orchestrator.batch_process(
            sharepoint_data=ground_truths,
            pdf_directory=args.pdf_dir,
            auto_correct=not args.no_correct
        )
        
        print("\n" + "="*70)
        print("BATCH PROCESSING COMPLETE")
        print("="*70)
        print(f"Total processed: {len(results)}")
        print(f"Total corrections: {sum(len(r['corrections_applied']) for r in results)}")


if __name__ == "__main__":
    main()

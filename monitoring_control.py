import pandas as pd
import numpy as np # Added import for numpy
import logging
from database_manager import db_manager # Import the singleton database manager
from configuration import Config

# Set up logging for the Monitoring and Control Module
# BasicConfig is now handled in main.py for the application.
logger = logging.getLogger(__name__)

class MonitoringControl:
    """
    Compares actual project performance (cost, progress) against planned estimates
    and budgets. Calculates variances and identifies potential issues.
    """
    def __init__(self, db_m_instance): # Accept db_manager, remove default and global fallback
        """
        Initializes the MonitoringControl module.
        """
        if db_m_instance is None:
            raise ValueError("DatabaseManager instance is required for MonitoringControl.")
        self.db_manager = db_m_instance
        logger.info("Monitoring and Control module initialized with provided db_manager.")

    def get_project_baseline_data(self, project_id):
        """
        Retrieves all necessary baseline planning data for a given project.
        Includes estimated costs from WBS elements and budgeted amounts.
        """
        # Get estimated costs from WBS elements
        # Corrected to use schema.sql PascalCase: WBSElementID, WBSCode, Description, EstimatedCost, ProjectID
        wbs_query = """
        SELECT
            wbs.WBSElementID AS wbs_element_id,
            wbs.WBSCode AS wbs_code,
            wbs.Description AS wbs_description,
            wbs.EstimatedCost AS estimated_cost
        FROM wbs_elements wbs
        WHERE wbs.ProjectID = ?
        """
        wbs_rows = self.db_manager.execute_query(wbs_query, (project_id,), fetch_all=True)
        wbs_df = pd.DataFrame([dict(row) for row in wbs_rows]) if wbs_rows else pd.DataFrame()

        # Get budget data
        # Corrected to use schema.sql PascalCase: BudgetID, WBSElementID, BudgetType, Amount, ProjectID
        budget_query = """
        SELECT
            pb.BudgetID AS budget_id,
            pb.WBSElementID AS wbs_element_id,
            pb.BudgetType AS budget_category,
            pb.Amount AS estimated_amount
        FROM project_budgets pb
        WHERE pb.ProjectID = ?
        """
        budget_rows = self.db_manager.execute_query(budget_query, (project_id,), fetch_all=True)
        budget_df = pd.DataFrame([dict(row) for row in budget_rows]) if budget_rows else pd.DataFrame()

        # Join WBS and Budget data if needed, or return separately
        # For simplicity, we'll primarily use WBS estimated_cost as the baseline for comparison
        # budget_df might offer more granular categories.
        return wbs_df, budget_df

    def get_project_actual_data(self, project_id):
        """
        Retrieves all necessary actual performance data for a given project.
        Includes actual costs and progress updates.
        """
        # Get actual costs
        # Corrected to use schema.sql PascalCase: ActualCostID, WBSElementID, CostCategory, Description, Amount, TransactionDate, ProjectID
        actual_costs_query = """
        SELECT
            ac.ActualCostID AS actual_cost_id,
            ac.WBSElementID AS wbs_element_id,
            ac.CostCategory AS cost_category,
            ac.Description AS cost_description,
            ac.Amount AS amount,
            ac.TransactionDate AS transaction_date
        FROM actual_costs ac
        WHERE ac.ProjectID = ?
        """
        actual_costs_rows = self.db_manager.execute_query(actual_costs_query, (project_id,), fetch_all=True)
        actual_costs_df = pd.DataFrame([dict(row) for row in actual_costs_rows]) if actual_costs_rows else pd.DataFrame()

        # Get latest progress updates for each WBS element
        # Corrected to use schema.sql PascalCase: ProgressUpdateID, WBSElementID, CompletionPercentage, UpdateDate, Notes, ProjectID
        progress_query = """
        SELECT
            pu.ProgressUpdateID AS progress_id,
            pu.WBSElementID AS wbs_element_id,
            pu.CompletionPercentage AS completion_percentage,
            pu.UpdateDate AS update_date,
            pu.Notes AS notes
        FROM progress_updates pu
        INNER JOIN (
            SELECT
                WBSElementID AS wbs_element_id,
                MAX(UpdateDate) AS max_update_date
            FROM progress_updates
            WHERE ProjectID = ?
            GROUP BY WBSElementID
        ) AS latest_updates
        ON pu.WBSElementID = latest_updates.wbs_element_id
        AND pu.UpdateDate = latest_updates.max_update_date
        WHERE pu.ProjectID = ?
        """
        progress_rows = self.db_manager.execute_query(progress_query, (project_id, project_id), fetch_all=True)
        progress_df = pd.DataFrame([dict(row) for row in progress_rows]) if progress_rows else pd.DataFrame()

        return actual_costs_df, progress_df

    def analyze_cost_variance(self, project_id):
        """
        Calculates cost variance for each WBS element (Estimated Cost vs. Actual Cost).
        Cost Variance (CV) = Earned Value (EV) - Actual Cost (AC)
        For simplicity, Earned Value for a WBS element is (Completion % / 100) * Estimated Cost
        """
        wbs_df, _ = self.get_project_baseline_data(project_id)
        actual_costs_df, progress_df = self.get_project_actual_data(project_id)

        if wbs_df.empty:
            logger.warning(f"No WBS baseline data for project {project_id}. Cannot analyze cost variance.")
            return pd.DataFrame(), "No baseline data available."

        if actual_costs_df.empty and progress_df.empty:
            logger.info(f"No actual cost or progress data for project {project_id}. Cost variance is N/A.")
            return wbs_df.assign(actual_cost=0.0, earned_value=0.0, cost_variance=0.0, cv_percentage=0.0), "No actuals to compare."


        # Sum actual costs by WBS element
        actual_costs_summary = actual_costs_df.groupby('wbs_element_id')['amount'].sum().reset_index()
        actual_costs_summary.rename(columns={'amount': 'total_actual_cost'}, inplace=True)

        # Merge WBS with actual costs
        variance_df = pd.merge(wbs_df, actual_costs_summary, on='wbs_element_id', how='left')
        variance_df['total_actual_cost'] = variance_df['total_actual_cost'].fillna(0)

        # Merge with latest progress for EV calculation
        variance_df = pd.merge(variance_df, progress_df[['wbs_element_id', 'completion_percentage']],
                               on='wbs_element_id', how='left')
        variance_df['completion_percentage'] = variance_df['completion_percentage'].fillna(0) # Assume 0% if no progress reported

        # Calculate Earned Value (EV)
        # EV = (BAC * PC) where BAC is Budget at Completion (Estimated Cost) and PC is Percent Complete
        variance_df['earned_value'] = (variance_df['completion_percentage'] / 100) * variance_df['estimated_cost']

        # Calculate Cost Variance (CV) = EV - AC
        variance_df['cost_variance'] = variance_df['earned_value'] - variance_df['total_actual_cost']

        # Calculate Cost Variance Percentage = (CV / EV) * 100
        # Handle division by zero if EV is 0
        variance_df['cv_percentage'] = variance_df.apply(
            lambda row: (row['cost_variance'] / row['earned_value'] * 100) if row['earned_value'] != 0 else np.nan,
            axis=1
        )

        logger.info(f"Cost variance analysis completed for project {project_id}.")
        return variance_df[['wbs_code', 'wbs_description', 'estimated_cost', 'total_actual_cost',
                             'completion_percentage', 'earned_value', 'cost_variance', 'cv_percentage']], "Cost variance analysis complete."

    def analyze_schedule_variance(self, project_id):
        """
        Analyzes schedule variance. This is a simplified approach as we don't have
        detailed schedules yet. We'll use Estimated Cost and Progress %.
        Schedule Variance (SV) = Earned Value (EV) - Planned Value (PV)
        For simplicity, Planned Value (PV) is the cumulative planned cost at a given point in time.
        Without detailed scheduling, we'll assume PV for an item is its Estimated Cost.
        A more robust SV needs a schedule baseline. Here, we'll just check if actual progress
        is behind or ahead of 100% completion relative to the estimated cost.
        """
        wbs_df, _ = self.get_project_baseline_data(project_id)
        _, progress_df = self.get_project_actual_data(project_id)

        if wbs_df.empty or progress_df.empty:
            logger.warning(f"No WBS baseline or progress data for project {project_id}. Cannot analyze schedule variance.")
            return pd.DataFrame(), "No baseline or progress data available."

        # Merge WBS with latest progress
        schedule_df = pd.merge(wbs_df, progress_df[['wbs_element_id', 'completion_percentage']],
                               on='wbs_element_id', how='left')
        schedule_df['completion_percentage'] = schedule_df['completion_percentage'].fillna(0)

        # Planned Value (PV): For simplification, consider PV as estimated cost for a fully planned item.
        # This will need a true schedule to be accurate.
        schedule_df['planned_value'] = schedule_df['estimated_cost']

        # Earned Value (EV) = (Completion % / 100) * Estimated Cost
        schedule_df['earned_value'] = (schedule_df['completion_percentage'] / 100) * schedule_df['estimated_cost']

        # Schedule Variance (SV) = EV - PV
        # If EV is less than PV, it indicates a schedule delay (relative to planned spending/work completion)
        schedule_df['schedule_variance'] = schedule_df['earned_value'] - schedule_df['planned_value']

        # Schedule Performance Index (SPI) = EV / PV
        schedule_df['spi'] = schedule_df.apply(
            lambda row: (row['earned_value'] / row['planned_value']) if row['planned_value'] != 0 else np.nan,
            axis=1
        )
        # Interpret SPI: SPI > 1 (ahead of schedule), SPI < 1 (behind schedule), SPI = 1 (on schedule)

        logger.info(f"Schedule variance analysis completed for project {project_id}.")
        return schedule_df[['wbs_code', 'wbs_description', 'estimated_cost', 'completion_percentage',
                            'earned_value', 'planned_value', 'schedule_variance', 'spi']], "Schedule variance analysis complete."

    def get_project_summary_performance(self, project_id):
        """
        Provides an overall summary of project performance (Cost and Schedule Performance Indexes).
        This sums up the values from detailed WBS analysis.
        """
        cost_variance_df, _ = self.analyze_cost_variance(project_id)
        schedule_variance_df, _ = self.analyze_schedule_variance(project_id)

        if cost_variance_df.empty or schedule_variance_df.empty:
            return {}, "Insufficient data for project summary performance."

        total_earned_value_cost = cost_variance_df['earned_value'].sum()
        total_actual_cost = cost_variance_df['total_actual_cost'].sum()
        total_estimated_cost = cost_variance_df['estimated_cost'].sum() # BAC (Budget at Completion)

        total_earned_value_schedule = schedule_variance_df['earned_value'].sum()
        total_planned_value_schedule = schedule_variance_df['planned_value'].sum()

        cpi = total_earned_value_cost / total_actual_cost if total_actual_cost != 0 else np.nan
        spi = total_earned_value_schedule / total_planned_value_schedule if total_planned_value_schedule != 0 else np.nan

        summary = {
            'project_id': project_id,
            'total_estimated_cost_baseline': total_estimated_cost,
            'total_actual_cost_incurred': total_actual_cost,
            'total_earned_value': total_earned_value_cost,
            'cost_performance_index_cpi': cpi,
            'schedule_performance_index_spi': spi,
            'overall_cost_variance': total_earned_value_cost - total_actual_cost,
            'overall_schedule_variance': total_earned_value_schedule - total_planned_value_schedule
        }

        # Suggest corrective actions based on CPI/SPI
        suggestions = []
        if cpi < 0.95: # Arbitrary threshold for concern
            suggestions.append("Cost Performance Index (CPI) is low. Review cost expenditures, look for cost-saving opportunities, and re-estimate remaining work.")
        elif cpi > 1.05:
            suggestions.append("Cost Performance Index (CPI) is high. This might indicate over-estimation or efficient cost management. Review to ensure accuracy.")
        else:
            suggestions.append("Cost Performance Index (CPI) is within acceptable range.")

        if spi < 0.95:
            suggestions.append("Schedule Performance Index (SPI) is low. Review schedule, identify critical path delays, and consider resource acceleration or re-baselining.")
        elif spi > 1.05:
            suggestions.append("Schedule Performance Index (SPI) is high. Project might be ahead of schedule. Review to confirm and potentially re-align resources.")
        else:
            suggestions.append("Schedule Performance Index (SPI) is within acceptable range.")

        summary['suggestions'] = suggestions

        logger.info(f"Overall performance summary generated for project {project_id}.")
        return summary, "Project summary performance complete."


if __name__ == "__main__":
    # This block demonstrates how the MonitoringControl module can be used.

    print("--- Testing Monitoring and Control Module ---")

    # Ensure a clean database for testing the full flow
    import os
    from integration import Integration
    from data_processing import DataProcessing
    from project_planning import ProjectPlanning
    from execution_management import ExecutionManagement
    from database_manager import DatabaseManager

    test_db_path = Config.get_database_path()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"Cleaned up existing database at: {test_db_path}")

    # Initialize DatabaseManager (singleton)
    _ = DatabaseManager()

    # --- Phase 1 & 2 & early Phase 3: Simulate Data Ingestion, Processing, Planning, and Execution ---
    sample_csv_path = os.path.join(Config.get_data_dir(), 'sample_estimate_for_monitoring.csv')
    sample_data = {
        'Cost Code': ['01-010', '02-100', '03-200', '03-210', '04-300'],
        'Description': ['Mobilization', 'Site Prep', 'Concrete Footings', 'Concrete Slab', 'Framing'],
        'Quantity': [1.0, 500.0, 15.0, 200.0, 100.0],
        'Unit': ['LS', 'SY', 'CY', 'SF', 'LF'],
        'Unit Cost': [5000.00, 15.00, 300.00, 5.00, 10.00],
        'Total Cost': [5000.00, 7500.00, 4500.00, 1000.00, 1000.00],
        'Phase': ['Pre-Construction', 'Foundation', 'Foundation', 'Foundation', 'Structure']
    }
    sample_df = pd.DataFrame(sample_data)
    sample_df.to_csv(sample_csv_path, index=False)

    integration_module = Integration()
    integration_module.import_estimate_from_csv(sample_csv_path)

    data_processor = DataProcessing()
    data_processor.process_estimate_data()

    project_planner = ProjectPlanning()
    project_id, _ = project_planner.create_project("New Office Building", "2025-07-01", "2026-06-30")
    if not project_id:
        print("Failed to create project, exiting test for Monitoring & Control.")
        exit()

    project_planner.generate_wbs_from_estimates(project_id)
    project_planner.generate_project_budget(project_id)
    project_planner.allocate_resources(project_id)

    # Fetch some WBS elements to use for tracking
    wbs_elements = project_planner.get_wbs_for_project(project_id)
    if wbs_elements.empty:
        print("No WBS elements found for the project. Cannot proceed with Monitoring & Control tests.")
        exit()

    # Map WBS codes to their IDs for easier access in tests
    wbs_map = {row['wbs_code']: row['id'] for index, row in wbs_elements.iterrows()}
    wbs_mobilization_id = wbs_map.get('01-010')
    wbs_site_prep_id = wbs_map.get('02-100')
    wbs_concrete_footings_id = wbs_map.get('03-200')
    wbs_concrete_slab_id = wbs_map.get('03-210')
    wbs_framing_id = wbs_map.get('04-300')


    exec_manager = ExecutionManagement()

    # --- Simulate Execution Data (Actual Costs and Progress) ---
    print("\n--- Simulating Actuals for Monitoring ---")

    # Mobilization (01-010): Estimated 5000.00
    exec_manager.record_actual_cost(project_id, wbs_mobilization_id, 'Labor', 'Mobilization Crew', 3000.00, '2025-07-05')
    exec_manager.record_actual_cost(project_id, wbs_mobilization_id, 'Equipment', 'Equipment Rent', 2500.00, '2025-07-06')
    exec_manager.record_progress_update(project_id, wbs_mobilization_id, 100.0, '2025-07-07', 'Mobilization completed (over budget)')

    # Site Prep (02-100): Estimated 7500.00
    exec_manager.record_actual_cost(project_id, wbs_site_prep_id, 'Subcontractor', 'Grading Sub', 5000.00, '2025-07-10')
    exec_manager.record_actual_cost(project_id, wbs_site_prep_id, 'Material', 'Fill Dirt', 1500.00, '2025-07-12')
    exec_manager.record_progress_update(project_id, wbs_site_prep_id, 75.0, '2025-07-15', 'Site prep 75% complete')

    # Concrete Footings (03-200): Estimated 4500.00
    exec_manager.record_actual_cost(project_id, wbs_concrete_footings_id, 'Labor', 'Concrete Crew', 2000.00, '2025-07-20')
    exec_manager.record_actual_cost(project_id, wbs_concrete_footings_id, 'Material', 'Concrete Delivery', 1000.00, '2025-07-20')
    exec_manager.record_progress_update(project_id, wbs_concrete_footings_id, 50.0, '2025-07-22', 'Footings 50% done')

    # Concrete Slab (03-210): Estimated 1000.00 (No actuals, no progress yet to show 0/N/A)
    # Framing (04-300): Estimated 1000.00 (No actuals, but 100% progress to show ahead of actuals for SV)
    exec_manager.record_progress_update(project_id, wbs_framing_id, 100.0, '2025-07-25', 'Framing magically finished early!')


    # --- Monitoring and Control ---
    monitor_control = MonitoringControl()

    print("\n--- Analyzing Cost Variance ---")
    cost_variance_results, cv_msg = monitor_control.analyze_cost_variance(project_id)
    print(f"Cost Variance Status: {cv_msg}")
    if not cost_variance_results.empty:
        print(cost_variance_results.to_string(index=False)) # .to_string() for better display of full df
    else:
        print("No cost variance results.")

    print("\n--- Analyzing Schedule Variance ---")
    schedule_variance_results, sv_msg = monitor_control.analyze_schedule_variance(project_id)
    print(f"Schedule Variance Status: {sv_msg}")
    if not schedule_variance_results.empty:
        print(schedule_variance_results.to_string(index=False))
    else:
        print("No schedule variance results.")

    print("\n--- Project Summary Performance ---")
    summary_performance, summary_msg = monitor_control.get_project_summary_performance(project_id)
    print(f"Summary Status: {summary_msg}")
    if summary_performance:
        for key, value in summary_performance.items():
            if key == 'suggestions':
                print(f"{key.replace('_', ' ').title()}:")
                for suggestion in value:
                    print(f"  - {suggestion}")
            else:
                print(f"{key.replace('_', ' ').title()}: {value:.2f}" if isinstance(value, (int, float)) else f"{key.replace('_', ' ').title()}: {value}")
    else:
        print("No project summary performance data.")

    # Clean up test files and database
    if os.path.exists(sample_csv_path):
        os.remove(sample_csv_path)
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"\nCleaned up test database and sample CSV.")


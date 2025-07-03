import pandas as pd
import logging
import os
from database_manager import db_manager
from configuration import Config
from monitoring_control import MonitoringControl # To get performance analysis data
import numpy as np # Was missing, needed by MonitoringControl, good to have here too if pandas NaN is used

logger = logging.getLogger(__name__)

class Reporting:
    def __init__(self, db_m_instance, monitor_control_instance=None): # db_m_instance is now required
        if db_m_instance is None:
            raise ValueError("DatabaseManager instance is required for Reporting.")
        self.db_manager = db_m_instance
        # If monitor_control_instance is not provided, instantiate it using the provided db_m_instance
        self.monitor_control = monitor_control_instance if monitor_control_instance else MonitoringControl(db_m_instance=self.db_manager)
        os.makedirs(Config.get_reports_dir(), exist_ok=True)
        logger.info("Reporting module initialized with provided db_manager.")

    def _get_project_data_for_report(self, project_id):
        project_details_row = self.db_manager.execute_query(
            "SELECT *, ProjectName AS project_name, EstimatedCost AS total_estimated_cost FROM Projects WHERE ProjectID = ?", (project_id,), fetch_one=True
        )
        if not project_details_row:
            logger.warning(f"Project with ID {project_id} not found for reporting.")
            return None, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        project_details_dict = dict(project_details_row)

        wbs_query = "SELECT WBSElementID AS wbs_element_id, WBSCode AS wbs_code, Description AS description, EstimatedCost AS estimated_cost FROM wbs_elements WHERE ProjectID = ?"
        wbs_rows = self.db_manager.execute_query(wbs_query, (project_id,), fetch_all=True)
        wbs_df = pd.DataFrame([dict(row) for row in wbs_rows]) if wbs_rows else pd.DataFrame()

        budget_query = "SELECT BudgetID AS budget_id, WBSElementID AS wbs_element_id, BudgetType AS budget_category, Amount AS estimated_amount FROM project_budgets WHERE ProjectID = ?"
        budget_rows = self.db_manager.execute_query(budget_query, (project_id,), fetch_all=True)
        budget_df = pd.DataFrame([dict(row) for row in budget_rows]) if budget_rows else pd.DataFrame()

        actual_costs_query = "SELECT ActualCostID AS actual_cost_id, WBSElementID AS wbs_element_id, CostCategory AS cost_category, Description AS cost_description, Amount AS amount, TransactionDate AS transaction_date FROM actual_costs WHERE ProjectID = ?"
        actual_costs_rows = self.db_manager.execute_query(actual_costs_query, (project_id,), fetch_all=True)
        actual_costs_df = pd.DataFrame([dict(row) for row in actual_costs_rows]) if actual_costs_rows else pd.DataFrame()

        _, progress_df = self.monitor_control.get_project_actual_data(project_id)
        return project_details_dict, wbs_df, budget_df, actual_costs_df, progress_df

    def generate_estimate_vs_actual_report(self, project_id):
        logger.info(f"Generating Estimate vs. Actual report for Project ID: {project_id}")
        project_details, wbs_df, _, actual_costs_df, _ = self._get_project_data_for_report(project_id)

        if project_details is None:
            return pd.DataFrame(), False, "Project data not found for report generation."
        if wbs_df.empty:
            logger.info(f"No WBS elements for project {project_id}. Report will be empty.")
            return pd.DataFrame(), True, "No WBS elements found for the project; report is empty."

        actual_costs_wbs_summary = pd.DataFrame()
        if not actual_costs_df.empty and 'wbs_element_id' in actual_costs_df.columns and 'amount' in actual_costs_df.columns:
            actual_costs_wbs_summary = actual_costs_df.groupby('wbs_element_id')['amount'].sum().reset_index()
            actual_costs_wbs_summary.rename(columns={'amount': 'total_actual_cost'}, inplace=True)

        if 'wbs_element_id' not in wbs_df.columns:
            logger.error("Critical: 'wbs_element_id' not found in wbs_df after _get_project_data_for_report.")
            return pd.DataFrame(), False, "Internal error: WBS DataFrame missing key column."

        if not actual_costs_wbs_summary.empty:
            report_df = pd.merge(wbs_df[['wbs_code', 'description', 'estimated_cost', 'wbs_element_id']],
                                 actual_costs_wbs_summary,
                                 on='wbs_element_id', how='left')
        else:
            report_df = wbs_df[['wbs_code', 'description', 'estimated_cost', 'wbs_element_id']].copy()
            report_df['total_actual_cost'] = 0.0

        report_df.rename(columns={'description': 'WBS Description'}, inplace=True)
        report_df['total_actual_cost'] = report_df['total_actual_cost'].fillna(0.0)

        report_df['estimated_cost'] = pd.to_numeric(report_df['estimated_cost'], errors='coerce').fillna(0.0)

        report_df['Variance'] = report_df['estimated_cost'] - report_df['total_actual_cost']
        report_df['Variance (%)'] = (report_df['Variance'] / report_df['estimated_cost'].replace(0, np.nan) * 100)

        project_level_actuals = 0.0
        if not actual_costs_df.empty and 'wbs_element_id' in actual_costs_df.columns and 'amount' in actual_costs_df.columns:
            # Sum actuals not tied to a WBS element
            project_level_actuals = actual_costs_df[actual_costs_df['wbs_element_id'].isnull()]['amount'].sum()


        if project_details.get('total_estimated_cost', 0.0) > 0 or project_level_actuals > 0:
            project_total_estimated_from_wbs = report_df[report_df['wbs_code'] != 'PROJECT_TOTAL']['estimated_cost'].sum()
            project_total_estimated = project_details.get('total_estimated_cost', project_total_estimated_from_wbs) #This should be ProjectDetails.EstimatedCost

            current_wbs_actuals_sum = report_df[report_df['wbs_code'] != 'PROJECT_TOTAL']['total_actual_cost'].sum()
            project_total_actual = current_wbs_actuals_sum + project_level_actuals

            project_variance = project_total_estimated - project_total_actual
            project_variance_percent = (project_variance / project_total_estimated * 100) if project_total_estimated != 0 else 0.0

            project_summary_row_data = {
                'wbs_code': 'PROJECT_TOTAL',
                'WBS Description': project_details.get('project_name', 'Overall Project'), # project_name from alias
                'estimated_cost': project_total_estimated,
                'total_actual_cost': project_total_actual,
                'Variance': project_variance,
                'Variance (%)': project_variance_percent
            }
            columns_for_summary = [col for col in report_df.columns if col != 'wbs_element_id']
            project_summary_row_df = pd.DataFrame([project_summary_row_data], columns=columns_for_summary)
            report_df_display = report_df[columns_for_summary]
            report_df_display = pd.concat([report_df_display, project_summary_row_df], ignore_index=True)
        else:
            report_df_display = report_df[[col for col in report_df.columns if col != 'wbs_element_id']]

        formatted_df = report_df_display.copy()
        for col in ['estimated_cost', 'total_actual_cost', 'Variance']:
            if col in formatted_df.columns:
                 formatted_df[col] = formatted_df[col].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "$0.00")
        if 'Variance (%)' in formatted_df.columns:
            formatted_df['Variance (%)'] = formatted_df['Variance (%)'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) and x != np.inf and x != -np.inf else "N/A")

        logger.info(f"Estimate vs. Actual report generated for Project ID: {project_id}.")
        return formatted_df, True, "Estimate vs. Actual report generated successfully."

    def generate_performance_report(self, project_id):
        logger.info(f"Generating Performance report for Project ID: {project_id}")
        cost_df, cv_msg = self.monitor_control.analyze_cost_variance(project_id)
        schedule_df, sv_msg = self.monitor_control.analyze_schedule_variance(project_id)
        summary, summary_msg = self.monitor_control.get_project_summary_performance(project_id)

        if not isinstance(summary, dict):
            logger.error(f"Failed to get performance summary for project {project_id}: {summary_msg}")
            return "", False, f"Failed to get performance summary: {summary_msg}"

        report_content = []
        report_content.append(f"Project Performance Report for: {summary.get('project_id', 'N/A')}\n")
        report_content.append("--------------------------------------------------\n")

        for key, value in summary.items():
            if key == 'suggestions':
                continue
            val_str = f"{value:.2f}" if isinstance(value, (float, np.floating)) and pd.notnull(value) else str(value)
            report_content.append(f"{key.replace('_', ' ').title()}: {val_str}\n")

        report_content.append("\nPerformance Suggestions:\n")
        for suggestion in summary.get('suggestions', []):
            report_content.append(f"- {suggestion}\n")
        report_content.append("\n--------------------------------------------------\n")
        report_content.append("Detailed Cost Variance (by WBS):\n")
        report_content.append(cost_df.to_string(index=False) + "\n\n")
        report_content.append("Detailed Schedule Variance (by WBS):\n")
        report_content.append(schedule_df.to_string(index=False) + "\n\n")

        full_report_text = "".join(report_content)
        logger.info(f"Performance report generated for Project ID: {project_id}.")
        return full_report_text, True, "Performance report generated successfully."

    def export_report(self, report_data, report_type, project_id, format='excel'):
        report_filename_base = f"project_{project_id}_{report_type.replace(' ', '_').lower()}_report"

        reports_dir = Config.get_reports_dir()
        os.makedirs(reports_dir, exist_ok=True)

        if format.lower() == 'excel' and isinstance(report_data, pd.DataFrame):
            output_path = os.path.join(reports_dir, report_filename_base + '.xlsx')
            try:
                report_data.to_excel(output_path, sheet_name=report_type, index=False)
                logger.info(f"Report '{report_type}' exported to Excel: {output_path}")
                return True, f"Report exported to {output_path}"
            except Exception as e:
                logger.error(f"Error exporting report to Excel '{output_path}': {e}", exc_info=True)
                return False, f"Failed to export report to Excel: {e}"
        elif format.lower() == 'text' and isinstance(report_data, str):
            output_path = os.path.join(reports_dir, report_filename_base + '.txt')
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report_data)
                logger.info(f"Report '{report_type}' exported to Text: {output_path}")
                return True, f"Report exported to {output_path}"
            except Exception as e:
                logger.error(f"Error exporting report to text '{output_path}': {e}", exc_info=True)
                return False, f"Failed to export report to text: {e}"
        else:
            logger.warning(f"Unsupported report format '{format}' or data type for '{report_type}' report.")
            return False, "Unsupported report format or data type for export."

    def generate_foreman_daily_summary(self, project_id: int, employee_id: int = None, log_date: str = None):
        """
        Generates a daily summary report for a Foreman, showing tasks and material usage.
        Filters by project_id, and optionally by employee_id and log_date.
        """
        logger.info(f"Generating Foreman Daily Summary for Project ID: {project_id}, Employee ID: {employee_id}, Date: {log_date}")

        query = """
        SELECT
            DL.LogDate,
            DL.JobSite,
            DL.HoursWorked,
            E.FirstName, E.LastName,
            DLT.TaskDescription, DLT.IsCompleted,
            DLM.MaterialDescription, DLM.Quantity, DLM.Unit, DLM.Type AS MaterialType,
            DLO.ObservationType, DLO.Description AS ObservationDescription
        FROM DailyLogs DL
        JOIN Employees E ON DL.EmployeeID = E.EmployeeID
        LEFT JOIN DailyLogTasks DLT ON DL.DailyLogID = DLT.DailyLogID
        LEFT JOIN DailyLogMaterials DLM ON DL.DailyLogID = DLM.DailyLogID
        LEFT JOIN DailyLogObservations DLO ON DL.DailyLogID = DLO.DailyLogID
        WHERE DL.ProjectID = ?
        """
        params = [project_id]

        if employee_id:
            query += " AND DL.EmployeeID = ?"
            params.append(employee_id)
        if log_date:
            query += " AND DL.LogDate = ?"
            params.append(log_date)

        query += " ORDER BY DL.LogDate DESC, E.LastName, E.FirstName;"

        rows = self.db_manager.execute_query(query, tuple(params), fetch_all=True)

        if not rows:
            return pd.DataFrame(), False, "No daily log data found for the specified criteria."

        df = pd.DataFrame([dict(row) for row in rows])

        # Group and format the data for a readable summary
        summary_lines = []
        for (log_date, employee_first, employee_last), group_df in df.groupby(['LogDate', 'FirstName', 'LastName']):
            summary_lines.append(f"\n--- Daily Summary for {employee_first} {employee_last} on {log_date} ---")
            summary_lines.append(f"Job Site: {group_df['JobSite'].iloc[0]}")
            summary_lines.append(f"Hours Worked: {group_df['HoursWorked'].iloc[0]:.1f}")

            tasks_completed = group_df[group_df['IsCompleted'] == 1]['TaskDescription'].dropna().unique()
            tasks_ongoing = group_df[group_df['IsCompleted'] == 0]['TaskDescription'].dropna().unique()

            if len(tasks_completed) > 0:
                summary_lines.append("Completed Tasks:")
                for task in tasks_completed:
                    summary_lines.append(f"  - {task}")
            if len(tasks_ongoing) > 0:
                summary_lines.append("Ongoing Tasks:")
                for task in tasks_ongoing:
                    summary_lines.append(f"  - {task}")

            materials_used = group_df[group_df['MaterialType'] == 'Used']['MaterialDescription'].dropna().unique()
            materials_needed = group_df[group_df['MaterialType'] == 'Needed']['MaterialDescription'].dropna().unique()

            if len(materials_used) > 0:
                summary_lines.append("Materials Used:")
                for mat in materials_used:
                    summary_lines.append(f"  - {mat}")
            if len(materials_needed) > 0:
                summary_lines.append("Materials Needed:")
                for mat in materials_needed:
                    summary_lines.append(f"  - {mat}")

            safety_obs = group_df[group_df['ObservationType'] == 'Safety']['ObservationDescription'].dropna().unique()
            issues_obs = group_df[group_df['ObservationType'] == 'Issue']['ObservationDescription'].dropna().unique()
            tool_obs = group_df[group_df['ObservationType'] == 'Tool']['ObservationDescription'].dropna().unique()

            if len(safety_obs) > 0:
                summary_lines.append("Safety Observations:")
                for obs in safety_obs:
                    summary_lines.append(f"  - {obs}")
            if len(issues_obs) > 0:
                summary_lines.append("Issues/Blockers:")
                for obs in issues_obs:
                    summary_lines.append(f"  - {obs}")
            if len(tool_obs) > 0:
                summary_lines.append("Tool Notes:")
                for obs in tool_obs:
                    summary_lines.append(f"  - {obs}")

        full_summary_text = "\n".join(summary_lines)
        logger.info(f"Foreman Daily Summary generated for Project ID: {project_id}.")
        return full_summary_text, True, "Foreman Daily Summary generated successfully."

# __main__ block removed for brevity

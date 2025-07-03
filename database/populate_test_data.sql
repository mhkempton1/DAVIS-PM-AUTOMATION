-- SQL Script to Populate Test Data for PM System RBAC and Reporting Tests

-- Insert Access Roles (if not already present from schema.sql)
INSERT OR IGNORE INTO AccessRoles (RoleName, Description) VALUES
('admin', 'System Administrator'),
('foreman', 'Manages field tasks and daily logs'),
('electrician', 'Records daily work and observations');

-- Insert Labor Levels
INSERT OR IGNORE INTO LaborLevels (LevelName, Description) VALUES
('Journeyman', 'Certified Electrician'),
('Apprentice', 'Apprentice Electrician'),
('Foreman', 'Lead Electrician on site'),
('Helper', 'General Labor Support');

-- Insert Task Tags
INSERT OR IGNORE INTO TaskTags (Tag, Description) VALUES
('phase/ri', 'Rough-In Phase'),
('phase/finish', 'Finish Phase'),
('phase/ug', 'Underground Phase'),
('phase/site', 'Site Work Phase'),
('phase/slab', 'Slab Work Phase'),
('phase/lv', 'Low Voltage Phase'),
('milestones', 'Project Milestones'),
('orders', 'Material Orders'),
('todo', 'To Do Item'),
('changes', 'Change Order Related');

-- Insert Test Employees (linked to AccessRoles)
-- EmployeeID 1: Admin (linked to 'admin' role)
INSERT OR IGNORE INTO Employees (EmployeeID, FirstName, LastName, Title, WorkEmail, AccessRoleID) VALUES
(1, 'Admin', 'User', 'System Administrator', 'admin@daviselectric.com', (SELECT AccessRoleID FROM AccessRoles WHERE RoleName = 'admin'));

-- EmployeeID 2: Foreman (linked to 'foreman' role)
INSERT OR IGNORE INTO Employees (EmployeeID, FirstName, LastName, Title, WorkEmail, AccessRoleID) VALUES
(2, 'Frank', 'Foreman', 'Project Foreman', 'frank.foreman@daviselectric.com', (SELECT AccessRoleID FROM AccessRoles WHERE RoleName = 'foreman'));

-- EmployeeID 3: Electrician (linked to 'electrician' role)
INSERT OR IGNORE INTO Employees (EmployeeID, FirstName, LastName, Title, WorkEmail, AccessRoleID) VALUES
(3, 'Eddie', 'Electrician', 'Journeyman Electrician', 'eddie.electrician@daviselectric.com', (SELECT AccessRoleID FROM AccessRoles WHERE RoleName = 'electrician'));

-- Insert Test Users for Application Login (linked to EmployeeIDs if applicable, or just for login)
-- Passwords are 'password' for all test users
INSERT OR IGNORE INTO users (id, username, password_hash, role) VALUES
(1, 'admin', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'admin'); -- 'password' hashed
INSERT OR IGNORE INTO users (id, username, password_hash, role) VALUES
(2, 'foreman', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'foreman'); -- 'password' hashed
INSERT OR IGNORE INTO users (id, username, password_hash, role) VALUES
(3, 'electrician', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'electrician'); -- 'password' hashed

-- Insert a Test Project
INSERT OR IGNORE INTO Projects (ProjectID, ProjectName, CustomerID, ProjectStatusID, StartDate, EndDate, ProjectManagerEmployeeID, ForemanEmployeeID) VALUES
(101, 'Test Project Alpha', 1, (SELECT ProjectStatusID FROM ProjectStatuses WHERE StatusName = 'Active'), '2025-07-01', '2025-08-31', 1, 2);

-- Insert Sample Daily Log Entries
-- Log by Foreman Frank for Test Project Alpha
INSERT OR IGNORE INTO DailyLogs (DailyLogID, EmployeeID, ProjectID, LogDate, JobSite, HoursWorked, Notes) VALUES
(1, 2, 101, '2025-07-01', 'Test Project Alpha - Site A', 8.0, 'Initial site setup and material check.');

INSERT OR IGNORE INTO DailyLogTasks (DailyLogID, TaskDescription, IsCompleted) VALUES
(1, 'Site setup completed', 1),
(1, 'Material inventory check', 0);

INSERT OR IGNORE INTO DailyLogMaterials (DailyLogID, MaterialDescription, Type, Quantity, Unit) VALUES
(1, '100ft 12/2 Romex', 'Used', 100, 'ft'),
(1, 'Wire nuts', 'Needed', 1, 'box');

INSERT OR IGNORE INTO DailyLogObservations (DailyLogID, ObservationType, Description) VALUES
(1, 'Safety', 'Conducted tool box talk on ladder safety.'),
(1, 'Issue', 'Generator fuel low, reported to office.'),
(1, 'Tool', 'Drill battery not holding charge.');

-- Log by Electrician Eddie for Test Project Alpha
INSERT OR IGNORE INTO DailyLogs (DailyLogID, EmployeeID, ProjectID, LogDate, JobSite, HoursWorked, Notes) VALUES
(2, 3, 101, '2025-07-01', 'Test Project Alpha - Building B', 7.5, 'Rough-in work on second floor.');

INSERT OR IGNORE INTO DailyLogTasks (DailyLogID, TaskDescription, IsCompleted) VALUES
(2, 'Rough-in circuits for office 201', 1),
(2, 'Install junction boxes in hallway', 0);

INSERT OR IGNORE INTO DailyLogMaterials (DailyLogID, MaterialDescription, Type, Quantity, Unit) VALUES
(2, '50ft 1/2 EMT', 'Used', 50, 'ft'),
(2, '1/2 EMT connectors', 'Used', 20, 'pcs');

INSERT OR IGNORE INTO DailyLogObservations (DailyLogID, ObservationType, Description) VALUES
(2, 'Safety', 'Ensured proper PPE usage.'),
(2, 'Issue', 'Missing blueprint for section C.'),
(2, 'Tool', 'Impact driver bit broke.');

-- Log by Foreman Frank for Test Project Alpha (another day)
INSERT OR IGNORE INTO DailyLogs (DailyLogID, EmployeeID, ProjectID, LogDate, JobSite, HoursWorked, Notes) VALUES
(3, 2, 101, '2025-07-02', 'Test Project Alpha - Site A', 8.0, 'Supervision and coordination.');

INSERT OR IGNORE INTO DailyLogTasks (DailyLogID, TaskDescription, IsCompleted) VALUES
(3, 'Coordinated with GC', 1),
(3, 'Reviewed progress with Eddie', 1);

INSERT OR IGNORE INTO DailyLogMaterials (DailyLogID, MaterialDescription, Type, Quantity, Unit) VALUES
(3, 'None', 'Used', 0, 'N/A');

INSERT OR IGNORE INTO DailyLogObservations (DailyLogID, ObservationType, Description) VALUES
(3, 'Safety', 'Site clear of debris.'),
(3, 'Issue', 'None'),
(3, 'Tool', 'All tools accounted for.');

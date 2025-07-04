-- ========================================================================== --
--            SQL Script for Davis Electric ERD (v8 - Normalized)             --
-- ========================================================================== --
-- Purpose: Creates the database schema for Davis Electric operations.        --
-- Features: Schemas, NVARCHAR, Normalized Statuses & Employee Skills       --
-- Generated On: Friday, April 18, 2025 -- You're welcome! ;)               --
-- ========================================================================== --

-- Use the target database (Replace 'DavisElectricDB' with your actual DB name)
-- USE [DavisElectricDB];
-- GO

-- == Drop Objects In Reverse Order of Creation (Safety First!) ==
-- Drop procedures, functions, views first if they exist (none in this script yet)

PRINT 'Dropping existing tables and constraints (if they exist)...';

-- Drop constraints referencing HR tables before dropping HR tables
-- (Add any others that might reference these as your app evolves)

-- Drop tables with Foreign Keys pointing to other tables first
IF OBJECT_ID('Time.TimeEntries') IS NOT NULL DROP TABLE Time.TimeEntries;
IF OBJECT_ID('Projects.ChangeOrderLineItems') IS NOT NULL DROP TABLE Projects.ChangeOrderLineItems;
IF OBJECT_ID('Projects.ChangeOrders') IS NOT NULL DROP TABLE Projects.ChangeOrders;
IF OBJECT_ID('Projects.ProjectDocuments') IS NOT NULL DROP TABLE Projects.ProjectDocuments;
IF OBJECT_ID('Sales.EstimateLineItems') IS NOT NULL DROP TABLE Sales.EstimateLineItems;
IF OBJECT_ID('Sales.EstimateHeaders') IS NOT NULL DROP TABLE Sales.EstimateHeaders;
IF OBJECT_ID('Shipping.ShipmentManifestItems') IS NOT NULL DROP TABLE Shipping.ShipmentManifestItems;
IF OBJECT_ID('Sales.SalesOrderLineItems') IS NOT NULL DROP TABLE Sales.SalesOrderLineItems;
IF OBJECT_ID('Sales.SalesOrders') IS NOT NULL DROP TABLE Sales.SalesOrders;
IF OBJECT_ID('Purchasing.PurchaseOrderLineItems') IS NOT NULL DROP TABLE Purchasing.PurchaseOrderLineItems;
IF OBJECT_ID('Purchasing.PurchaseOrders') IS NOT NULL DROP TABLE Purchasing.PurchaseOrders;
IF OBJECT_ID('Core.Materials') IS NOT NULL DROP TABLE Core.Materials;
IF OBJECT_ID('Core.Vendors') IS NOT NULL DROP TABLE Core.Vendors;
IF OBJECT_ID('Projects.ToolAssignments') IS NOT NULL DROP TABLE Projects.ToolAssignments;
IF OBJECT_ID('Projects.ResourceAssignments') IS NOT NULL DROP TABLE Projects.ResourceAssignments;
IF OBJECT_ID('Projects.Tasks') IS NOT NULL DROP TABLE Projects.Tasks;
IF OBJECT_ID('Core.Tools') IS NOT NULL DROP TABLE Core.Tools;
IF OBJECT_ID('Core.ToolTypes') IS NOT NULL DROP TABLE Core.ToolTypes;
IF OBJECT_ID('Core.Vehicles') IS NOT NULL DROP TABLE Core.Vehicles;
IF OBJECT_ID('HR.EmployeeCertifications') IS NOT NULL DROP TABLE HR.EmployeeCertifications;
IF OBJECT_ID('HR.EmployeeTrainingRecords') IS NOT NULL DROP TABLE HR.EmployeeTrainingRecords;
IF OBJECT_ID('HR.EmployeeEquipmentQualifications') IS NOT NULL DROP TABLE HR.EmployeeEquipmentQualifications;
IF OBJECT_ID('HR.Employees') IS NOT NULL DROP TABLE HR.Employees;
IF OBJECT_ID('HR.AccessRoles') IS NOT NULL DROP TABLE HR.AccessRoles;
IF OBJECT_ID('HR.CertificationTypes') IS NOT NULL DROP TABLE HR.CertificationTypes;
IF OBJECT_ID('HR.TrainingTypes') IS NOT NULL DROP TABLE HR.TrainingTypes;
IF OBJECT_ID('HR.EquipmentQualifications') IS NOT NULL DROP TABLE HR.EquipmentQualifications;
IF OBJECT_ID('Projects.Projects') IS NOT NULL DROP TABLE Projects.Projects;
IF OBJECT_ID('Sales.CustomerContacts') IS NOT NULL DROP TABLE Sales.CustomerContacts;
IF OBJECT_ID('Sales.Customers') IS NOT NULL DROP TABLE Sales.Customers;

-- Drop Prefabrication Link table if it exists (depends on Projects.Tasks and Prefabrication.Assemblies)
IF OBJECT_ID('Projects.TaskAssemblyAssignments') IS NOT NULL DROP TABLE Projects.TaskAssemblyAssignments;

-- Drop Prefabrication tables
IF OBJECT_ID('Prefabrication.AssemblyItems') IS NOT NULL DROP TABLE Prefabrication.AssemblyItems;
IF OBJECT_ID('Prefabrication.Assemblies') IS NOT NULL DROP TABLE Prefabrication.Assemblies;

-- Drop Lookup Tables
IF OBJECT_ID('Core.CustomerTypes') IS NOT NULL DROP TABLE Core.CustomerTypes;
IF OBJECT_ID('Core.ProjectStatuses') IS NOT NULL DROP TABLE Core.ProjectStatuses;
IF OBJECT_ID('Core.ProjectTypes') IS NOT NULL DROP TABLE Core.ProjectTypes;
IF OBJECT_ID('Core.TaskStatuses') IS NOT NULL DROP TABLE Core.TaskStatuses;
IF OBJECT_ID('Core.ToolStatuses') IS NOT NULL DROP TABLE Core.ToolStatuses;
IF OBJECT_ID('Core.OrderStatuses') IS NOT NULL DROP TABLE Core.OrderStatuses;
IF OBJECT_ID('Core.VendorTypes') IS NOT NULL DROP TABLE Core.VendorTypes;
IF OBJECT_ID('Core.AssemblyStatuses') IS NOT NULL DROP TABLE Core.AssemblyStatuses; -- Added
IF OBJECT_ID('Core.AssemblyTypes') IS NOT NULL DROP TABLE Core.AssemblyTypes; -- Added


-- Drop Schemas (if they are empty)
IF SCHEMA_ID('Prefabrication') IS NOT NULL DROP SCHEMA Prefabrication; -- Added Prefabrication
IF SCHEMA_ID('Time') IS NOT NULL DROP SCHEMA Time;
IF SCHEMA_ID('Shipping') IS NOT NULL DROP SCHEMA Shipping;
IF SCHEMA_ID('Purchasing') IS NOT NULL DROP SCHEMA Purchasing;
IF SCHEMA_ID('Sales') IS NOT NULL DROP SCHEMA Sales;
IF SCHEMA_ID('Projects') IS NOT NULL DROP SCHEMA Projects;
IF SCHEMA_ID('HR') IS NOT NULL DROP SCHEMA HR;
IF SCHEMA_ID('Core') IS NOT NULL DROP SCHEMA Core; -- Drop Core last as it might contain shared lookups

PRINT 'Finished dropping objects.';
GO

-- == Create Schemas ==
PRINT 'Creating Schemas...';
CREATE SCHEMA Core;
GO
CREATE SCHEMA HR;
GO
CREATE SCHEMA Projects;
GO
CREATE SCHEMA Sales;
GO
CREATE SCHEMA Purchasing;
GO
CREATE SCHEMA Shipping;
GO
CREATE SCHEMA Time;
GO
CREATE SCHEMA Prefabrication; -- New Schema for Prefabrication
GO
PRINT 'Schemas created.';

-- == Create Lookup Tables (Core Schema) ==
PRINT 'Creating Lookup Tables...';

CREATE TABLE Core.CustomerTypes (
    CustomerTypeID INT IDENTITY(1,1) PRIMARY KEY,
    TypeName NVARCHAR(100) NOT NULL UNIQUE,
    Description NVARCHAR(255) NULL
);
INSERT INTO Core.CustomerTypes (TypeName, Description) VALUES
('Commercial', 'Standard Commercial Client'),
('Residential', 'Individual Residential Client'),
('General Contractor', 'Acts as GC'),
('Industrial', 'Industrial Facility Client');

CREATE TABLE Core.ProjectStatuses (
    ProjectStatusID INT IDENTITY(1,1) PRIMARY KEY,
    StatusName NVARCHAR(50) NOT NULL UNIQUE,
    Description NVARCHAR(255) NULL
);
INSERT INTO Core.ProjectStatuses (StatusName, Description) VALUES
('Prospect', 'Potential project, pre-bid'),
('Bidding', 'Currently in the bidding phase'),
('Awarded', 'Project awarded, pre-start'),
('Active', 'Project is currently in progress'),
('On Hold', 'Project is temporarily paused'),
('Completed', 'All work finished'),
('Cancelled', 'Project cancelled'),
('Warranty', 'Project complete, under warranty period');


CREATE TABLE Core.ProjectTypes (
    ProjectTypeID INT IDENTITY(1,1) PRIMARY KEY,
    TypeName NVARCHAR(100) NOT NULL UNIQUE,
    Description NVARCHAR(255) NULL
);
INSERT INTO Core.ProjectTypes (TypeName, Description) VALUES
('New Construction', 'Ground-up new building'),
('Tenant Improvement', 'Interior build-out or remodel'),
('Service Call', 'Minor repair or service work'),
('Design-Build', 'Project including design phase'),
('Infrastructure', 'Site work, utilities, etc.');


CREATE TABLE Core.TaskStatuses (
    TaskStatusID INT IDENTITY(1,1) PRIMARY KEY,
    StatusName NVARCHAR(50) NOT NULL UNIQUE,
    Description NVARCHAR(255) NULL
);
INSERT INTO Core.TaskStatuses (StatusName, Description) VALUES
('Pending', 'Task created, not yet started'),
('Assigned', 'Task assigned to resource(s)'),
('In Progress', 'Task is actively being worked on'),
('Blocked', 'Task progress is impeded'),
('Completed', 'Task finished'),
('Cancelled', 'Task will not be performed');


CREATE TABLE Core.ToolStatuses (
    ToolStatusID INT IDENTITY(1,1) PRIMARY KEY,
    StatusName NVARCHAR(50) NOT NULL UNIQUE,
    Description NVARCHAR(255) NULL
);
INSERT INTO Core.ToolStatuses (StatusName, Description) VALUES
('Available', 'In stock, ready for assignment'),
('Assigned', 'Checked out to a project or employee'),
('Damaged', 'Tool is damaged and needs repair'),
('Under Repair', 'Tool is currently being repaired'),
('Missing', 'Tool location unknown'),
('Retired', 'Tool removed from service');


CREATE TABLE Core.OrderStatuses (
    OrderStatusID INT IDENTITY(1,1) PRIMARY KEY,
    StatusName NVARCHAR(50) NOT NULL UNIQUE,
    AppliesToPO BIT NOT NULL DEFAULT 0, -- True if usable for Purchase Orders
    AppliesToSO BIT NOT NULL DEFAULT 0  -- True if usable for Sales Orders
);
INSERT INTO Core.OrderStatuses (StatusName, AppliesToPO, AppliesToSO) VALUES
('Draft', 1, 1),
('Submitted', 1, 1), -- PO submitted to Vendor, SO submitted for approval
('Approved', 1, 1), -- PO approved internally, SO approved
('Vendor Acknowledged', 1, 0), -- Vendor confirmed PO receipt
('Partially Received', 1, 0),
('Received', 1, 0),
('Partially Shipped', 0, 1),
('Shipped', 0, 1),
('Invoiced', 1, 1),
('Paid', 1, 1),
('Cancelled', 1, 1),
('Closed', 1, 1); -- Final state after all activity


CREATE TABLE Core.VendorTypes (
    VendorTypeID INT IDENTITY(1,1) PRIMARY KEY,
    TypeName NVARCHAR(100) NOT NULL UNIQUE,
    Description NVARCHAR(255) NULL
);
INSERT INTO Core.VendorTypes (TypeName, Description) VALUES
('Material Supplier', 'Provides electrical materials'),
('Subcontractor', 'Performs specific work packages'),
('Equipment Rental', 'Provides rental equipment'),
('Service Provider', 'Provides other services (e.g., IT, Accounting)');

PRINT 'Lookup Tables created.';
GO

-- == Create Prefabrication Lookup Tables (Core Schema) ==
PRINT 'Creating Prefabrication Lookup Tables...';

CREATE TABLE Core.AssemblyStatuses (
    AssemblyStatusID INT IDENTITY(1,1) PRIMARY KEY,
    StatusName NVARCHAR(50) NOT NULL UNIQUE,
    Description NVARCHAR(255) NULL
);
INSERT INTO Core.AssemblyStatuses (StatusName, Description) VALUES
('Planning', 'Assembly design and planning phase'),
('Ready for Production', 'All components available, ready for fabrication'),
('In Production', 'Assembly is currently being fabricated'),
('Quality Check', 'Assembly undergoing quality control'),
('Ready for Staging', 'Assembly fabricated and passed QC, ready for project staging'),
('Staged', 'Assembly moved to project staging area'),
('Installed', 'Assembly installed at the project site'),
('Cancelled', 'Assembly production cancelled');

CREATE TABLE Core.AssemblyTypes (
    AssemblyTypeID INT IDENTITY(1,1) PRIMARY KEY,
    TypeName NVARCHAR(100) NOT NULL UNIQUE,
    Description NVARCHAR(255) NULL
);
INSERT INTO Core.AssemblyTypes (TypeName, Description) VALUES
('Wall Rough-in Assembly', 'Prefabricated electrical components for wall rough-in'),
('Fixture Assembly', 'Prefabricated light fixture assemblies with whips'),
('Panelboard Assembly', 'Prefabricated panelboard and components'),
('Skid Assembly', 'Electrical equipment mounted on a skid');

PRINT 'Prefabrication Lookup Tables created.';
GO


-- == Create Core Tables ==
PRINT 'Creating Core Tables (Vendors, Materials, Tools, Vehicles)...';

CREATE TABLE Core.Vendors (
    VendorID INT IDENTITY(1,1) PRIMARY KEY,
    VendorName NVARCHAR(255) NOT NULL UNIQUE,
    VendorTypeID INT NULL,
    ContactPerson NVARCHAR(255) NULL,
    PhoneNumber VARCHAR(50) NULL, -- Phone numbers often have specific formats, VARCHAR ok
    EmailAddress NVARCHAR(255) NULL,
    Website NVARCHAR(255) NULL,
    Address_Street NVARCHAR(255) NULL,
    Address_City NVARCHAR(100) NULL,
    Address_State NVARCHAR(50) NULL,
    Address_ZipCode VARCHAR(20) NULL, -- Zip codes have specific formats, VARCHAR ok
    AccountNumber NVARCHAR(100) NULL,
    DefaultPaymentTerms NVARCHAR(100) NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_Vendors_VendorTypes FOREIGN KEY (VendorTypeID) REFERENCES Core.VendorTypes(VendorTypeID)
);

CREATE TABLE Core.Materials (
    MaterialID INT IDENTITY(1,1) PRIMARY KEY,
    MaterialName NVARCHAR(255) NOT NULL UNIQUE,
    Description NVARCHAR(500) NULL,
    Manufacturer NVARCHAR(100) NULL,
    PartNumber NVARCHAR(100) NULL, -- Part numbers can be alphanumeric, NVARCHAR safer
    UnitOfMeasure NVARCHAR(20) NOT NULL,
    DefaultCost DECIMAL(18, 4) NULL,
    DefaultPrice DECIMAL(18, 4) NULL,
    Category NVARCHAR(100) NULL,
    IsInventoried BIT NOT NULL DEFAULT 0,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE()
);
CREATE INDEX IX_Materials_PartNumber ON Core.Materials (PartNumber);

CREATE TABLE Core.ToolTypes (
    ToolTypeID INT IDENTITY(1,1) PRIMARY KEY,
    TypeName NVARCHAR(150) NOT NULL UNIQUE,
    Category NVARCHAR(100) NULL,
    DefaultItemNumber NVARCHAR(100) NULL, -- Item numbers can be alphanumeric
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE()
);
CREATE INDEX IX_ToolTypes_DefaultItemNumber ON Core.ToolTypes (DefaultItemNumber);

CREATE TABLE Core.Tools (
    ToolID INT IDENTITY(1,1) PRIMARY KEY,
    ToolTypeID INT NULL,
    ToolSpecificMarking NVARCHAR(100) NOT NULL UNIQUE, -- E.g., Asset Tag or Serial#
    ItemNumber NVARCHAR(100) NULL, -- Inherited or specific Item#
    ToolStatusID INT NULL,
    PurchaseDate DATE NULL,
    PurchasePrice DECIMAL(10, 2) NULL,
    CurrentCondition NVARCHAR(100) NULL,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_Tools_ToolTypes FOREIGN KEY (ToolTypeID) REFERENCES Core.ToolTypes(ToolTypeID),
    CONSTRAINT FK_Tools_ToolStatuses FOREIGN KEY (ToolStatusID) REFERENCES Core.ToolStatuses(ToolStatusID)
);
CREATE INDEX IX_Tools_ItemNumber ON Core.Tools (ItemNumber);
CREATE INDEX IX_Tools_ToolStatusID ON Core.Tools (ToolStatusID);

CREATE TABLE Core.Vehicles (
    VehicleID INT IDENTITY(1,1) PRIMARY KEY,
    VehicleName NVARCHAR(100) NOT NULL UNIQUE, -- E.g., Truck 10, Van 5
    VehicleType NVARCHAR(50) NOT NULL, -- E.g., Pickup Truck, Cargo Van, Bucket Truck
    LicensePlate VARCHAR(20) NULL UNIQUE,
    VIN VARCHAR(17) NULL UNIQUE,
    Make NVARCHAR(100) NULL,
    Model NVARCHAR(100) NULL,
    Year INT NULL,
    Status NVARCHAR(50) NOT NULL DEFAULT 'Available', -- Could normalize this too, but keeping simple for now
    DateAcquired DATE NULL,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE()
);

PRINT 'Core Tables created.';
GO

-- == Create HR Tables ==
PRINT 'Creating HR Tables (AccessRoles, Employees, Certs, Training)...';

CREATE TABLE HR.AccessRoles (
    AccessRoleID INT IDENTITY(1,1) PRIMARY KEY,
    RoleName NVARCHAR(100) NOT NULL UNIQUE,
    Description NVARCHAR(500) NULL,
    -- Permissions fields would go here (e.g., CanReadProjects BIT, CanEditTimeEntries BIT, etc.)
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE()
);
-- Optional: Add default roles
INSERT INTO HR.AccessRoles (RoleName, Description) VALUES
('Administrator', 'Full system access'),
('Project Manager', 'Manages projects, estimates, financials'),
('Foreman', 'Manages field tasks, time entries, assignments'),
('Electrician', 'Standard field employee access'),
('Office Staff', 'Access to administrative functions');


CREATE TABLE HR.Employees (
    EmployeeID INT IDENTITY(1,1) PRIMARY KEY,
    FirstName NVARCHAR(100) NOT NULL,
    LastName NVARCHAR(100) NOT NULL,
    Title NVARCHAR(100) NULL,
    DepartmentArea NVARCHAR(100) NULL,
    ReportsToEmployeeID INT NULL,
    Duties NVARCHAR(MAX) NULL, -- Changed to MAX for potentially long text
    Notes NVARCHAR(MAX) NULL,  -- Changed to MAX
    Position NVARCHAR(100) NULL,
    Strata NVARCHAR(50) NULL,
    Band NVARCHAR(50) NULL,
    SalaryLow DECIMAL(18, 2) NULL,
    SalaryHigh DECIMAL(18, 2) NULL,
    PhoneNumber VARCHAR(50) NULL,        -- Primary contact phone
    WorkEmail NVARCHAR(255) NULL UNIQUE, -- Primary work email
    ExakTimeID VARCHAR(100) NULL UNIQUE, -- Specific system ID
    IsActive BIT NOT NULL DEFAULT 1,
    HireDate DATE NULL,
    AccessRoleID INT NULL,

    -- Fields from user's additional list (that remain on Employee table)
    EmployeeCity NVARCHAR(100) NULL,          -- Home city
    MainEmail NVARCHAR(255) NULL,             -- Potentially personal or alternate email
    MainPhoneNumber VARCHAR(50) NULL,         -- Potentially personal or alternate phone
    PayrollDriverInfo NVARCHAR(255) NULL,     -- Notes related to payroll/driver status
    PerformanceEvalDueDate DATE NULL,
    ShirtSize VARCHAR(20) NULL,
    Card2025Info NVARCHAR(100) NULL,          -- Keeping flexible as meaning is unclear
    EducationBackground NVARCHAR(500) NULL,   -- Free text for education info
    ForemanStartDate DATE NULL,               -- Date first became foreman

    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_Employees_ReportsTo FOREIGN KEY (ReportsToEmployeeID) REFERENCES HR.Employees(EmployeeID), -- Self-ref needs careful handling if deleting
    CONSTRAINT FK_Employees_AccessRoles FOREIGN KEY (AccessRoleID) REFERENCES HR.AccessRoles(AccessRoleID)
);
-- Index for finding direct reports
CREATE INDEX IX_Employees_ReportsToEmployeeID ON HR.Employees (ReportsToEmployeeID);


-- Employee Certifications (Normalized)
CREATE TABLE HR.CertificationTypes (
    CertificationTypeID INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(150) NOT NULL UNIQUE,
    Description NVARCHAR(500) NULL
);
INSERT INTO HR.CertificationTypes (Name, Description) VALUES
('Electrical License', 'State or Local Electrical License'),
('OSHA 10', 'OSHA 10 Hour Certification'),
('OSHA 30', 'OSHA 30 Hour Certification'),
('First Aid/CPR', 'First Aid and CPR Certification'),
('BICSI Installer', 'BICSI Installation Certification'),
('BICSI Technician', 'BICSI Technician Certification'),
('BICSI RCDD', 'BICSI Registered Communications Distribution Designer');
-- Add more as needed

CREATE TABLE HR.EmployeeCertifications (
    EmployeeCertificationID INT IDENTITY(1,1) PRIMARY KEY,
    EmployeeID INT NOT NULL,
    CertificationTypeID INT NOT NULL,
    IssueDate DATE NULL,
    ExpiryDate DATE NULL,
    CertificationNumber NVARCHAR(100) NULL, -- E.g., License number
    Details NVARCHAR(255) NULL, -- For things like BICSI level or other notes
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_EmployeeCertifications_Employees FOREIGN KEY (EmployeeID) REFERENCES HR.Employees(EmployeeID) ON DELETE CASCADE, -- Cascade delete if employee is removed
    CONSTRAINT FK_EmployeeCertifications_CertificationTypes FOREIGN KEY (CertificationTypeID) REFERENCES HR.CertificationTypes(CertificationTypeID),
    CONSTRAINT UK_Employee_CertificationType UNIQUE (EmployeeID, CertificationTypeID) -- Usually an employee has only one of each cert type active
);
CREATE INDEX IX_EmployeeCertifications_ExpiryDate ON HR.EmployeeCertifications (ExpiryDate);


-- Employee Training Records (Normalized)
CREATE TABLE HR.TrainingTypes (
    TrainingTypeID INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(150) NOT NULL UNIQUE,
    IsPolicyAcknowledgement BIT NOT NULL DEFAULT 0, -- Flag if it's signing a policy vs attending training
    Description NVARCHAR(500) NULL
);
INSERT INTO HR.TrainingTypes (Name, IsPolicyAcknowledgement, Description) VALUES
-- Policies
('Arc Flash PPE Policy Signed', 1, 'Acknowledgement of Arc Flash PPE Policy'),
('Open Trench Policy Signed', 1, 'Acknowledgement of Open Trench / Excavation Policy'),
('Elevated Surfaces Policy Signed', 1, 'Acknowledgement of Elevated Surfaces / Fall Protection Policy'),
('Driving Policy & Video Completed', 1, 'Acknowledgement of Driving Policy and Watched Safety Video'),
-- Training
('Arc Flash PPE Competent Person', 0, 'Training for Arc Flash Competent Person'),
('Open Trench Competent Person', 0, 'Training for Open Trench / Excavation Competent Person'),
('Fall Protection Trained', 0, 'General Fall Protection Training'),
('Hazard Communication Trained', 0, 'Training on Hazard Communication Standards (HazCom)'),
('Respiratory Protection Trained', 0, 'Training on Respiratory Protection Equipment and Use'),
('Scaffolding Trained', 0, 'Training on Safe Scaffold Use'),
('Ladder Trained', 0, 'Training on Safe Ladder Use'),
('Lockout/Tagout Trained', 0, 'Training on Lockout/Tagout Procedures (LOTO)'),
('Power Industrial Truck Trained', 0, 'Training for Powered Industrial Trucks (e.g., Forklifts - general)'),
('PPE Eye & Face Protection Trained', 0, 'Training on Eye and Face Protection PPE'),
('Machine Guarding Trained', 0, 'Training on Machine Guarding Safety'),
('Little Giant Ladder Trained', 0, 'Specific training for Little Giant Ladders');
-- Add more as needed


CREATE TABLE HR.EmployeeTrainingRecords (
    EmployeeTrainingRecordID INT IDENTITY(1,1) PRIMARY KEY,
    EmployeeID INT NOT NULL,
    TrainingTypeID INT NOT NULL,
    CompletionDate DATE NOT NULL,
    ExpiryDate DATE NULL, -- If training expires
    Trainer NVARCHAR(150) NULL,
    Notes NVARCHAR(500) NULL,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_EmployeeTrainingRecords_Employees FOREIGN KEY (EmployeeID) REFERENCES HR.Employees(EmployeeID) ON DELETE CASCADE,
    CONSTRAINT FK_EmployeeTrainingRecords_TrainingTypes FOREIGN KEY (TrainingTypeID) REFERENCES HR.TrainingTypes(TrainingTypeID),
    CONSTRAINT UK_Employee_TrainingType_Completion UNIQUE (EmployeeID, TrainingTypeID, CompletionDate) -- Prevents duplicate records for same training on same day
);
CREATE INDEX IX_EmployeeTrainingRecords_ExpiryDate ON HR.EmployeeTrainingRecords (ExpiryDate);


-- Employee Equipment Qualifications (Normalized)
CREATE TABLE HR.EquipmentQualifications (
    EquipmentQualificationID INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL UNIQUE,
    Description NVARCHAR(500) NULL
);
INSERT INTO HR.EquipmentQualifications (Name, Description) VALUES
('Forklift', 'Standard Warehouse Forklift'),
('Scissor Lift', 'Aerial Work Platform - Scissor Type'),
('Jackhammer', 'Pneumatic or Electric Jackhammer Operation'),
('Tugger', 'Material Handling Tugger Vehicle'),
('LULL', 'Extended Reach Forklift / Telehandler (Lull is a brand name)'),
('Core Drill', 'Concrete Core Drilling Equipment'),
('Mini Excavator', 'Small Excavator Operation'),
('Backhoe', 'Backhoe Loader Operation'),
('Skid Steer', 'Skid Steer Loader Operation'),
('Cherry Picker', 'Aerial Work Platform - Boom Type (Often Vehicle Mounted)'),
('Man Lift', 'Aerial Work Platform - Articulated or Telescopic Boom Lift'),
('Boom Forklift', 'Telehandler / Extended Reach Forklift'),
('Trencher', 'Mechanical Trencher Operation');
-- Add more as needed

CREATE TABLE HR.EmployeeEquipmentQualifications (
    EmployeeEquipmentQualificationID INT IDENTITY(1,1) PRIMARY KEY,
    EmployeeID INT NOT NULL,
    EquipmentQualificationID INT NOT NULL,
    QualificationDate DATE NOT NULL, -- Date employee was deemed qualified
    QualifiedByEmployeeID INT NULL, -- Optional: Who qualified them?
    Notes NVARCHAR(500) NULL,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_EmployeeEquipmentQualifications_Employees FOREIGN KEY (EmployeeID) REFERENCES HR.Employees(EmployeeID) ON DELETE CASCADE,
    CONSTRAINT FK_EmployeeEquipmentQualifications_EquipmentQualifications FOREIGN KEY (EquipmentQualificationID) REFERENCES HR.EquipmentQualifications(EquipmentQualificationID),
    CONSTRAINT FK_EmployeeEquipmentQualifications_QualifiedBy FOREIGN KEY (QualifiedByEmployeeID) REFERENCES HR.Employees(EmployeeID), -- Can't self-reference FK easily here before Employees exists if dropping fully
    CONSTRAINT UK_Employee_EquipmentQualification UNIQUE (EmployeeID, EquipmentQualificationID) -- Usually qualified or not
);

PRINT 'HR Tables created.';
GO

-- == Create Sales Tables ==
PRINT 'Creating Sales Tables (Customers, Contacts, Orders, Estimates)...';

CREATE TABLE Sales.Customers (
    CustomerID BIGINT IDENTITY(1,1) PRIMARY KEY,
    CustomerName NVARCHAR(255) NOT NULL UNIQUE, -- Ensuring CustomerName is unique
    CustomerNumber VARCHAR(50) NULL UNIQUE, -- Adding a user-friendly Customer Number
    CustomerTypeID INT NULL,
    BillingAddress_Street NVARCHAR(255) NULL,
    BillingAddress_City NVARCHAR(100) NULL,
    BillingAddress_State NVARCHAR(50) NULL,
    BillingAddress_ZipCode VARCHAR(20) NULL,
    ShippingAddress_Street NVARCHAR(255) NULL, -- Added Shipping Address fields
    ShippingAddress_City NVARCHAR(100) NULL,
    ShippingAddress_State NVARCHAR(50) NULL,
    ShippingAddress_ZipCode VARCHAR(20) NULL,
    PhoneNumber VARCHAR(50) NULL, -- General phone for the customer entity
    EmailAddress NVARCHAR(255) NULL, -- General email for the customer entity
    Website NVARCHAR(255) NULL,
    QuickBooksCustomerID VARCHAR(100) NULL UNIQUE,
    DefaultPaymentTerms NVARCHAR(100) NULL,
    TaxExemptID NVARCHAR(100) NULL, -- For tax exemption information
    CreditLimit DECIMAL(18,2) NULL,
    Notes NVARCHAR(MAX) NULL, -- Increased size for more detailed notes
    IsActive BIT NOT NULL DEFAULT 1,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_Customers_CustomerTypes FOREIGN KEY (CustomerTypeID) REFERENCES Core.CustomerTypes(CustomerTypeID)
);
CREATE INDEX IX_Customers_CustomerName ON Sales.Customers (CustomerName);
CREATE INDEX IX_Customers_CustomerNumber ON Sales.Customers (CustomerNumber);

CREATE TABLE Sales.CustomerContacts (
    ContactID INT IDENTITY(1,1) PRIMARY KEY,
    CustomerID BIGINT NOT NULL,
    FirstName NVARCHAR(100) NOT NULL,
    LastName NVARCHAR(100) NULL,
    FullName AS (ISNULL(FirstName, '') + ' ' + ISNULL(LastName, '')) PERSISTED, -- Calculated FullName
    Title NVARCHAR(100) NULL,
    Department NVARCHAR(100) NULL, -- Added Department for the contact
    PhoneNumber VARCHAR(50) NULL,
    MobileNumber VARCHAR(50) NULL,
    Extension VARCHAR(20) NULL, -- Added Phone Extension
    EmailAddress NVARCHAR(255) NULL,
    PreferredContactMethod NVARCHAR(50) NULL, -- e.g., Email, Phone, Mobile
    IsPrimaryContact BIT NOT NULL DEFAULT 0,
    IsBillingContact BIT NOT NULL DEFAULT 0, -- Specific contact type flags
    IsShippingContact BIT NOT NULL DEFAULT 0,
    Notes NVARCHAR(MAX) NULL, -- Increased size for more detailed notes
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_CustomerContacts_Customers FOREIGN KEY (CustomerID) REFERENCES Sales.Customers(CustomerID) ON DELETE CASCADE -- Delete contacts if customer is deleted
);
CREATE INDEX IX_CustomerContacts_CustomerID ON Sales.CustomerContacts (CustomerID);
CREATE INDEX IX_CustomerContacts_EmailAddress ON Sales.CustomerContacts (EmailAddress);
CREATE INDEX IX_CustomerContacts_FullName ON Sales.CustomerContacts (FullName);


CREATE TABLE Sales.SalesOrders (
    SalesOrderID BIGINT IDENTITY(1,1) PRIMARY KEY,
    CustomerID BIGINT NOT NULL,
    ProjectID BIGINT NULL, -- Link to project if applicable
    SalesOrderNumber VARCHAR(100) NOT NULL UNIQUE, -- Needs a robust generation scheme
    CustomerPONumber NVARCHAR(100) NULL, -- Customer's PO ref for this SO
    OrderDate DATE NOT NULL,
    EmployeeID_Salesperson INT NULL,
    OrderStatusID INT NULL,
    Description NVARCHAR(1000) NULL,
    Subtotal DECIMAL(18, 2) NULL,
    TaxAmount DECIMAL(18, 2) NULL,
    TotalAmount DECIMAL(18, 2) NULL,
    Notes NVARCHAR(MAX) NULL, -- Changed to MAX
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_SalesOrders_Customers FOREIGN KEY (CustomerID) REFERENCES Sales.Customers(CustomerID),
    -- CONSTRAINT FK_SalesOrders_Projects FOREIGN KEY (ProjectID) REFERENCES Projects.Projects(ProjectID), -- Add this FK after Projects table exists
    CONSTRAINT FK_SalesOrders_Salesperson FOREIGN KEY (EmployeeID_Salesperson) REFERENCES HR.Employees(EmployeeID),
    CONSTRAINT FK_SalesOrders_OrderStatuses FOREIGN KEY (OrderStatusID) REFERENCES Core.OrderStatuses(OrderStatusID)
);
CREATE INDEX IX_SalesOrders_CustomerID ON Sales.SalesOrders (CustomerID);
CREATE INDEX IX_SalesOrders_ProjectID ON Sales.SalesOrders (ProjectID); -- Create index even if FK is deferred
CREATE INDEX IX_SalesOrders_OrderStatusID ON Sales.SalesOrders (OrderStatusID);


CREATE TABLE Sales.SalesOrderLineItems (
    SOLineItemID BIGINT IDENTITY(1,1) PRIMARY KEY,
    SalesOrderID BIGINT NOT NULL,
    LineNumber INT NOT NULL,
    MaterialID INT NULL,
    AssemblyID BIGINT NULL, -- Added AssemblyID to link to a prefabricated assembly
    ServiceID INT NULL, -- Placeholder for a potential future Core.Services table
    Description NVARCHAR(500) NOT NULL, -- Should maybe pull from Material/Service/Assembly but allow override
    Quantity DECIMAL(18, 4) NOT NULL,
    UnitOfMeasure NVARCHAR(20) NOT NULL,
    UnitPrice DECIMAL(18, 4) NOT NULL,
    LineTotal AS (ISNULL(Quantity * UnitPrice, 0)) PERSISTED, -- Calculated column
    Notes NVARCHAR(500) NULL,
    CONSTRAINT FK_SalesOrderLineItems_SalesOrders FOREIGN KEY (SalesOrderID) REFERENCES Sales.SalesOrders(SalesOrderID) ON DELETE CASCADE,
    CONSTRAINT FK_SalesOrderLineItems_Materials FOREIGN KEY (MaterialID) REFERENCES Core.Materials(MaterialID),
    CONSTRAINT FK_SalesOrderLineItems_Assemblies FOREIGN KEY (AssemblyID) REFERENCES Prefabrication.Assemblies(AssemblyID), -- Added FK to Assemblies
    -- CONSTRAINT FK_SalesOrderLineItems_Services FOREIGN KEY (ServiceID) REFERENCES Core.Services(ServiceID), -- Uncomment if Services table is added
    CONSTRAINT UK_SalesOrderLineItems_Line UNIQUE (SalesOrderID, LineNumber),
    CONSTRAINT CK_SalesOrderLineItems_ItemType CHECK (
        (MaterialID IS NOT NULL AND ServiceID IS NULL AND AssemblyID IS NULL) OR -- Material only
        (MaterialID IS NULL AND ServiceID IS NOT NULL AND AssemblyID IS NULL) OR -- Service only
        (MaterialID IS NULL AND ServiceID IS NULL AND AssemblyID IS NOT NULL) OR -- Assembly only
        (MaterialID IS NULL AND ServiceID IS NULL AND AssemblyID IS NULL) -- Manual line (Description only)
    )
);
CREATE INDEX IX_SalesOrderLineItems_MaterialID ON Sales.SalesOrderLineItems (MaterialID);
CREATE INDEX IX_SalesOrderLineItems_AssemblyID ON Sales.SalesOrderLineItems (AssemblyID); -- Added index for AssemblyID


-- Estimate tables are similar to Sales Orders but represent a quote/bid
CREATE TABLE Sales.EstimateHeaders (
    EstimateHeaderID BIGINT IDENTITY(1,1) PRIMARY KEY,
    EstimateNumber VARCHAR(100) NOT NULL UNIQUE,
    ProjectID BIGINT NULL, -- FK Added later
    CustomerID BIGINT NOT NULL,
    EstimateDate DATE NOT NULL,
    ExpiryDate DATE NULL,
    EmployeeID_Estimator INT NULL,
    Status NVARCHAR(50) NULL, -- Could normalize: Bidding, Submitted, Accepted, Rejected
    Description NVARCHAR(1000) NULL,
    Subtotal DECIMAL(18, 2) NULL,
    TaxAmount DECIMAL(18, 2) NULL,
    TotalAmount DECIMAL(18, 2) NULL,
    Notes NVARCHAR(MAX) NULL,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_EstimateHeaders_Customers FOREIGN KEY (CustomerID) REFERENCES Sales.Customers(CustomerID),
    CONSTRAINT FK_EstimateHeaders_Estimator FOREIGN KEY (EmployeeID_Estimator) REFERENCES HR.Employees(EmployeeID)
    -- CONSTRAINT FK_EstimateHeaders_Projects FOREIGN KEY (ProjectID) REFERENCES Projects.Projects(ProjectID) -- Add later
);
CREATE INDEX IX_EstimateHeaders_ProjectID ON Sales.EstimateHeaders (ProjectID);
CREATE INDEX IX_EstimateHeaders_CustomerID ON Sales.EstimateHeaders (CustomerID);


CREATE TABLE Sales.EstimateLineItems (
    EstimateLineItemID BIGINT IDENTITY(1,1) PRIMARY KEY,
    EstimateHeaderID BIGINT NOT NULL,
    LineNumber INT NOT NULL,
    MaterialID INT NULL,
    AssemblyID BIGINT NULL, -- Added AssemblyID
    ServiceID INT NULL, -- Placeholder
    Description NVARCHAR(500) NOT NULL,
    Quantity DECIMAL(18, 4) NOT NULL,
    UnitOfMeasure NVARCHAR(20) NOT NULL,
    UnitCost DECIMAL(18, 4) NULL, -- Cost for estimation
    UnitPrice DECIMAL(18, 4) NOT NULL, -- Price for estimation
    LineTotal AS (ISNULL(Quantity * UnitPrice, 0)) PERSISTED,
    Notes NVARCHAR(500) NULL,
    CONSTRAINT FK_EstimateLineItems_EstimateHeaders FOREIGN KEY (EstimateHeaderID) REFERENCES Sales.EstimateHeaders(EstimateHeaderID) ON DELETE CASCADE,
    CONSTRAINT FK_EstimateLineItems_Materials FOREIGN KEY (MaterialID) REFERENCES Core.Materials(MaterialID),
    CONSTRAINT FK_EstimateLineItems_Assemblies FOREIGN KEY (AssemblyID) REFERENCES Prefabrication.Assemblies(AssemblyID), -- Added FK to Assemblies
    -- CONSTRAINT FK_EstimateLineItems_Services FOREIGN KEY (ServiceID) REFERENCES Core.Services(ServiceID),
    CONSTRAINT UK_EstimateLineItems_Line UNIQUE (EstimateHeaderID, LineNumber),
    CONSTRAINT CK_EstimateLineItems_ItemType CHECK ( -- Similar check as in SalesOrderLineItems
        (MaterialID IS NOT NULL AND ServiceID IS NULL AND AssemblyID IS NULL) OR
        (MaterialID IS NULL AND ServiceID IS NOT NULL AND AssemblyID IS NULL) OR
        (MaterialID IS NULL AND ServiceID IS NULL AND AssemblyID IS NOT NULL) OR
        (MaterialID IS NULL AND ServiceID IS NULL AND AssemblyID IS NULL)
    )
);
CREATE INDEX IX_EstimateLineItems_MaterialID ON Sales.EstimateLineItems (MaterialID);
CREATE INDEX IX_EstimateLineItems_AssemblyID ON Sales.EstimateLineItems (AssemblyID); -- Added index for AssemblyID


PRINT 'Sales Tables created.';
GO

-- == Create Purchasing Tables ==
PRINT 'Creating Purchasing Tables...';

CREATE TABLE Purchasing.PurchaseOrders (
    PurchaseOrderID BIGINT IDENTITY(1,1) PRIMARY KEY,
    VendorID INT NOT NULL,
    ProjectID BIGINT NULL, -- FK Added later
    EmployeeID_Requester INT NULL,
    EmployeeID_Approver INT NULL,
    PONumber VARCHAR(100) NOT NULL UNIQUE, -- Needs robust generation scheme
    VendorOrderNumber NVARCHAR(100) NULL, -- Vendor's confirmation number
    OrderDate DATE NOT NULL,
    ExpectedDeliveryDate DATE NULL,
    ActualDeliveryDate DATE NULL,
    ShippingAddress_Street NVARCHAR(255) NULL,
    ShippingAddress_City NVARCHAR(100) NULL,
    ShippingAddress_State NVARCHAR(50) NULL,
    ShippingAddress_ZipCode VARCHAR(20) NULL,
    ShippingInstructions NVARCHAR(500) NULL,
    OrderStatusID INT NULL,
    Subtotal DECIMAL(18, 2) NULL,
    TaxAmount DECIMAL(18, 2) NULL,
    ShippingCost DECIMAL(18, 2) NULL,
    TotalAmount DECIMAL(18, 2) NULL,
    Notes NVARCHAR(MAX) NULL, -- Changed to MAX
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_PurchaseOrders_Vendors FOREIGN KEY (VendorID) REFERENCES Core.Vendors(VendorID),
    -- CONSTRAINT FK_PurchaseOrders_Projects FOREIGN KEY (ProjectID) REFERENCES Projects.Projects(ProjectID), -- Add later
    CONSTRAINT FK_PurchaseOrders_Requester FOREIGN KEY (EmployeeID_Requester) REFERENCES HR.Employees(EmployeeID),
    CONSTRAINT FK_PurchaseOrders_Approver FOREIGN KEY (EmployeeID_Approver) REFERENCES HR.Employees(EmployeeID),
    CONSTRAINT FK_PurchaseOrders_OrderStatuses FOREIGN KEY (OrderStatusID) REFERENCES Core.OrderStatuses(OrderStatusID)
);
CREATE INDEX IX_PurchaseOrders_VendorID ON Purchasing.PurchaseOrders (VendorID);
CREATE INDEX IX_PurchaseOrders_ProjectID ON Purchasing.PurchaseOrders (ProjectID); -- Create index even if FK is deferred
CREATE INDEX IX_PurchaseOrders_OrderStatusID ON Purchasing.PurchaseOrders (OrderStatusID);


CREATE TABLE Purchasing.PurchaseOrderLineItems (
    POLineItemID BIGINT IDENTITY(1,1) PRIMARY KEY,
    PurchaseOrderID BIGINT NOT NULL,
    LineNumber INT NOT NULL,
    MaterialID INT NULL,
    AssemblyID BIGINT NULL, -- Added AssemblyID for purchasing prefabricated assemblies (or components for them)
    Description NVARCHAR(500) NOT NULL, -- Pull from Material/Assembly or allow override
    QuantityOrdered DECIMAL(18, 4) NOT NULL,
    UnitOfMeasure NVARCHAR(20) NOT NULL,
    UnitPrice DECIMAL(18, 4) NOT NULL,
    LineTotal AS (ISNULL(QuantityOrdered * UnitPrice, 0)) PERSISTED,
    QuantityReceived DECIMAL(18, 4) NULL DEFAULT 0,
    DateLastReceived DATE NULL,
    Notes NVARCHAR(500) NULL,
    CONSTRAINT FK_PurchaseOrderLineItems_PurchaseOrders FOREIGN KEY (PurchaseOrderID) REFERENCES Purchasing.PurchaseOrders(PurchaseOrderID) ON DELETE CASCADE,
    CONSTRAINT FK_PurchaseOrderLineItems_Materials FOREIGN KEY (MaterialID) REFERENCES Core.Materials(MaterialID),
    CONSTRAINT FK_PurchaseOrderLineItems_Assemblies FOREIGN KEY (AssemblyID) REFERENCES Prefabrication.Assemblies(AssemblyID), -- Added FK to Assemblies
    CONSTRAINT UK_PurchaseOrderLineItems_Line UNIQUE (PurchaseOrderID, LineNumber),
    CONSTRAINT CK_PurchaseOrderLineItems_ItemType CHECK ( -- Can order materials, or assemblies, or describe non-catalog items
        (MaterialID IS NOT NULL AND AssemblyID IS NULL) OR
        (MaterialID IS NULL AND AssemblyID IS NOT NULL) OR
        (MaterialID IS NULL AND AssemblyID IS NULL)
    )
);
CREATE INDEX IX_PurchaseOrderLineItems_MaterialID ON Purchasing.PurchaseOrderLineItems (MaterialID);
CREATE INDEX IX_PurchaseOrderLineItems_AssemblyID ON Purchasing.PurchaseOrderLineItems (AssemblyID); -- Added index for AssemblyID

PRINT 'Purchasing Tables created.';
GO

-- == Create Projects Tables ==
PRINT 'Creating Projects Tables...';

CREATE TABLE Projects.Projects (
    ProjectID BIGINT IDENTITY(1,1) PRIMARY KEY,
    ProjectName NVARCHAR(255) NOT NULL,
    CustomerID BIGINT NOT NULL,
    ProjectNumber VARCHAR(100) NULL UNIQUE, -- Needs robust generation scheme
    Location_Street NVARCHAR(255) NULL,
    Location_City NVARCHAR(100) NULL,
    Location_State NVARCHAR(50) NULL,
    Location_ZipCode VARCHAR(20) NULL,
    ProjectStatusID INT NULL,
    ProjectTypeID INT NULL,
    StartDate DATE NULL,
    EndDate DATE NULL,
    ProjectManagerEmployeeID INT NULL,
    ForemanEmployeeID INT NULL,
    ContractAmount DECIMAL(18, 2) NULL,
    SquareFootage DECIMAL(10, 2) NULL,
    IncludesSiteWork BIT NULL,
    BidDueDate DATE NULL,
    BidPurpose NVARCHAR(255) NULL,
    DeliveryMethod NVARCHAR(100) NULL,
    IsTaxExempt BIT NULL,
    IsBondRequired BIT NULL,
    CCIP_OCIP_Flag VARCHAR(50) NULL, -- Keep as VARCHAR or normalize? Keeping simple for now.
    EstimatedCost DECIMAL(18, 2) NULL,
    EstimatedManHours DECIMAL(10, 2) NULL,
    EstimatedDuration DECIMAL(10, 2) NULL, -- In days? Weeks? Clarify unit. Assuming days.
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_Projects_Customers FOREIGN KEY (CustomerID) REFERENCES Sales.Customers(CustomerID),
    CONSTRAINT FK_Projects_ProjectManager FOREIGN KEY (ProjectManagerEmployeeID) REFERENCES HR.Employees(EmployeeID),
    CONSTRAINT FK_Projects_Foreman FOREIGN KEY (ForemanEmployeeID) REFERENCES HR.Employees(EmployeeID),
    CONSTRAINT FK_Projects_ProjectStatuses FOREIGN KEY (ProjectStatusID) REFERENCES Core.ProjectStatuses(ProjectStatusID),
    CONSTRAINT FK_Projects_ProjectTypes FOREIGN KEY (ProjectTypeID) REFERENCES Core.ProjectTypes(ProjectTypeID)
);
CREATE INDEX IX_Projects_CustomerID ON Projects.Projects (CustomerID);
CREATE INDEX IX_Projects_ProjectNumber ON Projects.Projects (ProjectNumber);
CREATE INDEX IX_Projects_ProjectStatusID ON Projects.Projects (ProjectStatusID);
CREATE INDEX IX_Projects_ProjectManagerEmployeeID ON Projects.Projects (ProjectManagerEmployeeID);
CREATE INDEX IX_Projects_ForemanEmployeeID ON Projects.Projects (ForemanEmployeeID);


CREATE TABLE Projects.Tasks (
    TaskID INT IDENTITY(1,1) PRIMARY KEY,
    ProjectID BIGINT NOT NULL,
    TaskType NVARCHAR(100) NOT NULL, -- Could normalize if list is fixed
    Description NVARCHAR(MAX) NOT NULL, -- Changed to MAX
    ScheduledStartDate DATETIME2 NULL,
    ScheduledEndDate DATETIME2 NULL,
    ActualStartDate DATETIME2 NULL,
    ActualEndDate DATETIME2 NULL,
    TaskStatusID INT NULL,
    Priority INT NULL, -- E.g., 1=High, 5=Low
    CreatedByEmployeeID INT NULL,
    ParentTaskID INT NULL, -- For sub-tasks
    EstimatedHours DECIMAL(10, 2) NULL,
    ActualHours DECIMAL(10, 2) NULL, -- Could be sum from TimeEntries
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_Tasks_Projects FOREIGN KEY (ProjectID) REFERENCES Projects.Projects(ProjectID) ON DELETE CASCADE,
    CONSTRAINT FK_Tasks_Employees FOREIGN KEY (CreatedByEmployeeID) REFERENCES HR.Employees(EmployeeID),
    CONSTRAINT FK_Tasks_TaskStatuses FOREIGN KEY (TaskStatusID) REFERENCES Core.TaskStatuses(TaskStatusID),
    CONSTRAINT FK_Tasks_ParentTask FOREIGN KEY (ParentTaskID) REFERENCES Projects.Tasks(TaskID) -- Self-ref for subtasks
);
CREATE INDEX IX_Tasks_ProjectID ON Projects.Tasks (ProjectID);
CREATE INDEX IX_Tasks_TaskStatusID ON Projects.Tasks (TaskStatusID);
CREATE INDEX IX_Tasks_ParentTaskID ON Projects.Tasks (ParentTaskID);


CREATE TABLE Projects.ResourceAssignments (
    AssignmentID BIGINT IDENTITY(1,1) PRIMARY KEY,
    TaskID INT NOT NULL,
    EmployeeID INT NOT NULL,
    VehicleID INT NULL, -- Assign a vehicle to the employee for this task?
    AssignedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    AssignmentStartDate DATETIME2 NULL, -- Planned start for this resource on this task
    AssignmentEndDate DATETIME2 NULL,   -- Planned end
    Notes NVARCHAR(500) NULL,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_ResourceAssignments_Tasks FOREIGN KEY (TaskID) REFERENCES Projects.Tasks(TaskID) ON DELETE CASCADE,
    CONSTRAINT FK_ResourceAssignments_Employees FOREIGN KEY (EmployeeID) REFERENCES HR.Employees(EmployeeID),
    CONSTRAINT FK_ResourceAssignments_Vehicles FOREIGN KEY (VehicleID) REFERENCES Core.Vehicles(VehicleID),
    CONSTRAINT UK_ResourceAssignments_Task_Employee UNIQUE (TaskID, EmployeeID) -- Assign employee to a task only once
);
CREATE INDEX IX_ResourceAssignments_EmployeeID ON Projects.ResourceAssignments (EmployeeID);
CREATE INDEX IX_ResourceAssignments_VehicleID ON Projects.ResourceAssignments (VehicleID);


CREATE TABLE Projects.ToolAssignments (
    ToolAssignmentID BIGINT IDENTITY(1,1) PRIMARY KEY,
    ToolID INT NOT NULL,
    ProjectID BIGINT NULL, -- Assigned to a project...
    AssignedToEmployeeID INT NULL, -- ...or directly to an employee
    AssignedByEmployeeID INT NULL,
    TaskID INT NULL, -- ...or specifically for a task
    DateAssigned DATETIME2 NOT NULL DEFAULT GETDATE(),
    ExpectedReturnDate DATE NULL,
    DateReturned DATETIME2 NULL,
    ReturnedByEmployeeID INT NULL,
    ConditionOut NVARCHAR(100) NULL,
    ConditionIn NVARCHAR(100) NULL,
    Notes NVARCHAR(MAX) NULL, -- Changed to MAX
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_ToolAssignments_Tools FOREIGN KEY (ToolID) REFERENCES Core.Tools(ToolID),
    CONSTRAINT FK_ToolAssignments_Projects FOREIGN KEY (ProjectID) REFERENCES Projects.Projects(ProjectID),
    CONSTRAINT FK_ToolAssignments_Tasks FOREIGN KEY (TaskID) REFERENCES Projects.Tasks(TaskID),
    CONSTRAINT FK_ToolAssignments_AssignedToEmployee FOREIGN KEY (AssignedToEmployeeID) REFERENCES HR.Employees(EmployeeID),
    CONSTRAINT FK_ToolAssignments_AssignedByEmployee FOREIGN KEY (AssignedByEmployeeID) REFERENCES HR.Employees(EmployeeID),
    CONSTRAINT FK_ToolAssignments_ReturnedByEmployee FOREIGN KEY (ReturnedByEmployeeID) REFERENCES HR.Employees(EmployeeID),
    CONSTRAINT CK_ToolAssignments_AssignmentTarget CHECK ( (ProjectID IS NOT NULL AND AssignedToEmployeeID IS NULL AND TaskID IS NULL) OR (ProjectID IS NULL AND AssignedToEmployeeID IS NOT NULL AND TaskID IS NULL) OR (ProjectID IS NULL AND AssignedToEmployeeID IS NULL AND TaskID IS NOT NULL) OR (ProjectID IS NOT NULL AND AssignedToEmployeeID IS NOT NULL AND TaskID IS NULL) OR (ProjectID IS NOT NULL AND AssignedToEmployeeID IS NULL AND TaskID IS NOT NULL) ) -- Ensure tool assigned to Project OR Employee OR Task, or maybe Proj+Emp or Proj+Task
    -- Simpler Check: At least one target must be specified
    -- CONSTRAINT CK_ToolAssignments_Target CHECK (ProjectID IS NOT NULL OR AssignedToEmployeeID IS NOT NULL OR TaskID IS NOT NULL)
    -- Even Simpler: Let's just allow combinations for now, maybe assigned to employee working on a project task. Remove complex check.
);
-- Find currently assigned tools (where DateReturned is null)
CREATE INDEX IX_ToolAssignments_ToolID_DateReturned ON Projects.ToolAssignments (ToolID) WHERE DateReturned IS NULL;
CREATE INDEX IX_ToolAssignments_ProjectID ON Projects.ToolAssignments (ProjectID);
CREATE INDEX IX_ToolAssignments_AssignedToEmployeeID ON Projects.ToolAssignments (AssignedToEmployeeID);
CREATE INDEX IX_ToolAssignments_TaskID ON Projects.ToolAssignments (TaskID);


-- Project Documents (Placeholder - might need more detail)
CREATE TABLE Projects.ProjectDocuments (
    ProjectDocumentID BIGINT IDENTITY(1,1) PRIMARY KEY,
    ProjectID BIGINT NOT NULL,
    DocumentName NVARCHAR(255) NOT NULL,
    DocumentType NVARCHAR(100) NULL, -- E.g., Drawing, Submittal, RFI, Photo
    FilePath NVARCHAR(1000) NOT NULL, -- Network path or URL
    UploadedByEmployeeID INT NULL,
    UploadDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    Description NVARCHAR(MAX) NULL,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_ProjectDocuments_Projects FOREIGN KEY (ProjectID) REFERENCES Projects.Projects(ProjectID) ON DELETE CASCADE,
    CONSTRAINT FK_ProjectDocuments_UploadedBy FOREIGN KEY (UploadedByEmployeeID) REFERENCES HR.Employees(EmployeeID)
);
CREATE INDEX IX_ProjectDocuments_ProjectID ON Projects.ProjectDocuments (ProjectID);


-- Change Orders (Basic Structure)
CREATE TABLE Projects.ChangeOrders (
    ChangeOrderID BIGINT IDENTITY(1,1) PRIMARY KEY,
    ProjectID BIGINT NOT NULL,
    ChangeOrderNumber VARCHAR(100) NOT NULL, -- E.g., CO-001
    Description NVARCHAR(MAX) NOT NULL,
    Status NVARCHAR(50) NOT NULL, -- E.g., Pending, Approved, Rejected, Executed
    RequestDate DATE NULL,
    ApprovalDate DATE NULL,
    Amount DECIMAL(18, 2) NOT NULL DEFAULT 0,
    CreatedByEmployeeID INT NULL,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_ChangeOrders_Projects FOREIGN KEY (ProjectID) REFERENCES Projects.Projects(ProjectID) ON DELETE CASCADE,
    CONSTRAINT FK_ChangeOrders_CreatedBy FOREIGN KEY (CreatedByEmployeeID) REFERENCES HR.Employees(EmployeeID),
    CONSTRAINT UK_ChangeOrders_Project_Number UNIQUE (ProjectID, ChangeOrderNumber)
);
CREATE INDEX IX_ChangeOrders_Status ON Projects.ChangeOrders (Status);

CREATE TABLE Projects.ChangeOrderLineItems (
    ChangeOrderLineItemID BIGINT IDENTITY(1,1) PRIMARY KEY,
    ChangeOrderID BIGINT NOT NULL,
    LineNumber INT NOT NULL,
    Description NVARCHAR(500) NOT NULL,
    MaterialID INT NULL,
    ServiceID INT NULL,
    Quantity DECIMAL(18, 4) NULL,
    UnitOfMeasure NVARCHAR(20) NULL,
    UnitPrice DECIMAL(18, 4) NULL,
    LineTotal DECIMAL(18, 2) NULL, -- Usually manually entered or calculated based on type
    Notes NVARCHAR(500) NULL,
    CONSTRAINT FK_ChangeOrderLineItems_ChangeOrders FOREIGN KEY (ChangeOrderID) REFERENCES Projects.ChangeOrders(ChangeOrderID) ON DELETE CASCADE,
    CONSTRAINT FK_ChangeOrderLineItems_Materials FOREIGN KEY (MaterialID) REFERENCES Core.Materials(MaterialID),
    -- CONSTRAINT FK_ChangeOrderLineItems_Services FOREIGN KEY (ServiceID) REFERENCES Core.Services(ServiceID),
    CONSTRAINT UK_ChangeOrderLineItems_Line UNIQUE (ChangeOrderID, LineNumber)
);

PRINT 'Projects Tables created.';
GO

-- == Create Shipping Table ==
PRINT 'Creating Shipping Table (Manifest)...';

CREATE TABLE Shipping.ShipmentManifestItems (
    ShipmentManifestItemID BIGINT IDENTITY(1,1) PRIMARY KEY,
    -- Link to a ShipmentHeader? Or directly to Task/Project? Assuming Task for now.
    TaskID INT NULL, -- Items shipped for a specific task (can be NULL if shipping general assembly)
    ProjectID BIGINT NOT NULL, -- Project is likely always known for a shipment
    MaterialID INT NULL,
    AssemblyID BIGINT NULL, -- Added AssemblyID for shipping completed assemblies
    ToolID INT NULL,
    QuantityShipped DECIMAL(18, 4) NOT NULL,
    UnitOfMeasure NVARCHAR(20) NULL, -- Should match Material/Assembly UoM if present
    ShipmentDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    ShippedByEmployeeID INT NULL,
    ReceivedBy NVARCHAR(255) NULL, -- Who received the shipment at site/customer
    TrackingNumber NVARCHAR(100) NULL, -- Carrier tracking number
    Notes NVARCHAR(500) NULL,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_ShipmentManifestItems_Tasks FOREIGN KEY (TaskID) REFERENCES Projects.Tasks(TaskID),
    CONSTRAINT FK_ShipmentManifestItems_Projects FOREIGN KEY (ProjectID) REFERENCES Projects.Projects(ProjectID), -- Added FK
    CONSTRAINT FK_ShipmentManifestItems_Materials FOREIGN KEY (MaterialID) REFERENCES Core.Materials(MaterialID),
    CONSTRAINT FK_ShipmentManifestItems_Assemblies FOREIGN KEY (AssemblyID) REFERENCES Prefabrication.Assemblies(AssemblyID), -- Added FK
    CONSTRAINT FK_ShipmentManifestItems_Tools FOREIGN KEY (ToolID) REFERENCES Core.Tools(ToolID),
    CONSTRAINT FK_ShipmentManifestItems_ShippedBy FOREIGN KEY (ShippedByEmployeeID) REFERENCES HR.Employees(EmployeeID),
    CONSTRAINT CK_ShipmentManifestItems_ItemType CHECK ( -- Must be one of Material, Assembly, or Tool
        (MaterialID IS NOT NULL AND AssemblyID IS NULL AND ToolID IS NULL) OR
        (MaterialID IS NULL AND AssemblyID IS NOT NULL AND ToolID IS NULL) OR
        (MaterialID IS NULL AND AssemblyID IS NULL AND ToolID IS NOT NULL)
    )
);
CREATE INDEX IX_ShipmentManifestItems_TaskID ON Shipping.ShipmentManifestItems (TaskID);
CREATE INDEX IX_ShipmentManifestItems_ProjectID ON Shipping.ShipmentManifestItems (ProjectID); -- Added Index
CREATE INDEX IX_ShipmentManifestItems_MaterialID ON Shipping.ShipmentManifestItems (MaterialID);
CREATE INDEX IX_ShipmentManifestItems_AssemblyID ON Shipping.ShipmentManifestItems (AssemblyID); -- Added Index
CREATE INDEX IX_ShipmentManifestItems_ToolID ON Shipping.ShipmentManifestItems (ToolID);


PRINT 'Shipping Table created.';
GO

-- == Create Time Tracking Table ==
PRINT 'Creating Time Tracking Table...';

CREATE TABLE Time.TimeEntries (
    TimeEntryID BIGINT IDENTITY(1,1) PRIMARY KEY,
    EmployeeID INT NOT NULL,
    ProjectID BIGINT NOT NULL,
    TaskID INT NULL, -- Optional: Link time to a specific task
    EntryDate DATE NOT NULL,
    HoursWorked DECIMAL(5, 2) NOT NULL,
    TimeCode NVARCHAR(50) NULL, -- E.g., Regular, Overtime, Travel (Could normalize)
    CostCode NVARCHAR(50) NULL, -- Link to specific cost code for job costing
    Notes NVARCHAR(500) NULL,
    IsApproved BIT NOT NULL DEFAULT 0,
    ApprovedByEmployeeID INT NULL,
    ApprovalDate DATETIME2 NULL,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_TimeEntries_Employees FOREIGN KEY (EmployeeID) REFERENCES HR.Employees(EmployeeID),
    CONSTRAINT FK_TimeEntries_Projects FOREIGN KEY (ProjectID) REFERENCES Projects.Projects(ProjectID),
    CONSTRAINT FK_TimeEntries_Tasks FOREIGN KEY (TaskID) REFERENCES Projects.Tasks(TaskID),
    CONSTRAINT FK_TimeEntries_ApprovedBy FOREIGN KEY (ApprovedByEmployeeID) REFERENCES HR.Employees(EmployeeID),
    CONSTRAINT CK_TimeEntries_HoursWorked CHECK (HoursWorked > 0 AND HoursWorked <= 24) -- Sanity check
);
CREATE INDEX IX_TimeEntries_Employee_Date ON Time.TimeEntries (EmployeeID, EntryDate);
CREATE INDEX IX_TimeEntries_Project_Date ON Time.TimeEntries (ProjectID, EntryDate);
CREATE INDEX IX_TimeEntries_TaskID ON Time.TimeEntries (TaskID);


PRINT 'Time Tracking Table created.';
GO

-- == Create Prefabrication Tables ==
PRINT 'Creating Prefabrication Tables...';

CREATE TABLE Prefabrication.Assemblies (
    AssemblyID BIGINT IDENTITY(1,1) PRIMARY KEY,
    AssemblyName NVARCHAR(255) NOT NULL,
    AssemblyNumber VARCHAR(100) NULL UNIQUE, -- Similar to ProjectNumber or CustomerNumber
    AssemblyTypeID INT NULL,
    AssemblyStatusID INT NULL,
    ProjectID BIGINT NULL, -- Link to the project this assembly is for
    DrawingReference NVARCHAR(255) NULL, -- Link to specific drawing or model
    EstimatedHours DECIMAL(10,2) NULL, -- Estimated hours to produce this assembly
    ActualHours DECIMAL(10,2) NULL, -- Actual hours spent
    ProductionStartDate DATE NULL,
    ProductionEndDate DATE NULL,
    TargetInstallationDate DATE NULL,
    Notes NVARCHAR(MAX) NULL,
    CreatedByEmployeeID INT NULL,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_Assemblies_AssemblyTypes FOREIGN KEY (AssemblyTypeID) REFERENCES Core.AssemblyTypes(AssemblyTypeID),
    CONSTRAINT FK_Assemblies_AssemblyStatuses FOREIGN KEY (AssemblyStatusID) REFERENCES Core.AssemblyStatuses(AssemblyStatusID),
    CONSTRAINT FK_Assemblies_Projects FOREIGN KEY (ProjectID) REFERENCES Projects.Projects(ProjectID),
    CONSTRAINT FK_Assemblies_CreatedByEmployee FOREIGN KEY (CreatedByEmployeeID) REFERENCES HR.Employees(EmployeeID)
);
CREATE INDEX IX_Assemblies_AssemblyNumber ON Prefabrication.Assemblies (AssemblyNumber);
CREATE INDEX IX_Assemblies_ProjectID ON Prefabrication.Assemblies (ProjectID);
CREATE INDEX IX_Assemblies_AssemblyStatusID ON Prefabrication.Assemblies (AssemblyStatusID);
CREATE INDEX IX_Assemblies_AssemblyTypeID ON Prefabrication.Assemblies (AssemblyTypeID);

CREATE TABLE Prefabrication.AssemblyItems (
    AssemblyItemID BIGINT IDENTITY(1,1) PRIMARY KEY,
    AssemblyID BIGINT NOT NULL,
    MaterialID INT NOT NULL,
    Quantity DECIMAL(18,4) NOT NULL,
    UnitOfMeasure NVARCHAR(20) NOT NULL, -- Should align with Core.Materials.UnitOfMeasure
    Notes NVARCHAR(500) NULL,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_AssemblyItems_Assemblies FOREIGN KEY (AssemblyID) REFERENCES Prefabrication.Assemblies(AssemblyID) ON DELETE CASCADE,
    CONSTRAINT FK_AssemblyItems_Materials FOREIGN KEY (MaterialID) REFERENCES Core.Materials(MaterialID)
);
CREATE INDEX IX_AssemblyItems_AssemblyID ON Prefabrication.AssemblyItems (AssemblyID);
CREATE INDEX IX_AssemblyItems_MaterialID ON Prefabrication.AssemblyItems (MaterialID);

-- Link Assemblies to Project Tasks (e.g., Task for "Install Prefab Assembly X")
CREATE TABLE Projects.TaskAssemblyAssignments (
    TaskAssemblyAssignmentID BIGINT IDENTITY(1,1) PRIMARY KEY,
    TaskID INT NOT NULL,
    AssemblyID BIGINT NOT NULL,
    Notes NVARCHAR(500) NULL,
    DateCreated DATETIME2 NOT NULL DEFAULT GETDATE(),
    LastModifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_TaskAssemblyAssignments_Tasks FOREIGN KEY (TaskID) REFERENCES Projects.Tasks(TaskID) ON DELETE CASCADE,
    CONSTRAINT FK_TaskAssemblyAssignments_Assemblies FOREIGN KEY (AssemblyID) REFERENCES Prefabrication.Assemblies(AssemblyID) ON DELETE CASCADE,
    CONSTRAINT UK_TaskAssemblyAssignments_Task_Assembly UNIQUE (TaskID, AssemblyID) -- Ensure an assembly is assigned to a task only once
);
CREATE INDEX IX_TaskAssemblyAssignments_AssemblyID ON Projects.TaskAssemblyAssignments (AssemblyID);


PRINT 'Prefabrication Tables created.';
GO


-- == Add Deferred Foreign Keys ==
-- Add FKs that cross schema boundaries or depend on tables created later
PRINT 'Adding deferred Foreign Key constraints...';

ALTER TABLE Sales.SalesOrders
ADD CONSTRAINT FK_SalesOrders_Projects FOREIGN KEY (ProjectID) REFERENCES Projects.Projects(ProjectID);
GO

ALTER TABLE Sales.EstimateHeaders
ADD CONSTRAINT FK_EstimateHeaders_Projects FOREIGN KEY (ProjectID) REFERENCES Projects.Projects(ProjectID);
GO

ALTER TABLE Purchasing.PurchaseOrders
ADD CONSTRAINT FK_PurchaseOrders_Projects FOREIGN KEY (ProjectID) REFERENCES Projects.Projects(ProjectID);
GO

-- Might need others depending on exact dependencies, e.g., ShipmentManifestItems to Projects?

PRINT 'Deferred Foreign Keys added.';
GO

-- ========================================================================== --
--                           SCRIPT COMPLETE                                  --
--        Don't forget to populate your lookup tables thoughtfully!           --
-- ========================================================================== --
PRINT '*** Database Schema Creation Script Completed Successfully! ***';

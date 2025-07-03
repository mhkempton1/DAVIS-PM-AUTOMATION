-- ========================================================================== --
--            SQL Script for Davis Electric ERD (v8 - Normalized)             --
-- Purpose: Creates the database schema for Davis Electric operations.        --
-- Features: Schemas, NVARCHAR, Normalized Statuses & Employee Skills       --
-- Generated On: Friday, April 18, 2025 -- You're welcome! ;)               --
-- ========================================================================== --

-- == Drop Objects In Reverse Order of Creation (Safety First!) ==
DROP TABLE IF EXISTS LaborLevels; -- New
DROP TABLE IF EXISTS TaskTags; -- New
DROP TABLE IF EXISTS Production_Assembly_Tracking; -- New
DROP TABLE IF EXISTS Purchasing_Log; -- New
DROP TABLE IF EXISTS LLM_Parsed_Data_Log; -- New
DROP TABLE IF EXISTS TimeEntries;
DROP TABLE IF EXISTS ChangeOrderLineItems;
DROP TABLE IF EXISTS ChangeOrders;
DROP TABLE IF EXISTS ProjectDocuments;
DROP TABLE IF EXISTS EstimateLineItems;
DROP TABLE IF EXISTS EstimateHeaders;
DROP TABLE IF EXISTS ShipmentManifestItems;
DROP TABLE IF EXISTS SalesOrderLineItems;
DROP TABLE IF EXISTS SalesOrders;
DROP TABLE IF EXISTS PurchaseOrderLineItems;
DROP TABLE IF EXISTS PurchaseOrders;
DROP TABLE IF EXISTS AssemblyComponents; -- Drop before Assemblies and Materials
DROP TABLE IF EXISTS Assemblies;         -- Drop before Materials (if it had direct FKs, though not in this design)
DROP TABLE IF EXISTS Materials;
DROP TABLE IF EXISTS Vendors;
DROP TABLE IF EXISTS ToolAssignments;
DROP TABLE IF EXISTS ResourceAssignments;
DROP TABLE IF EXISTS TaskMaterialRequirements; -- Drop before Tasks, Assemblies, Materials
DROP TABLE IF EXISTS Tasks;
DROP TABLE IF EXISTS Tools;
DROP TABLE IF EXISTS ToolTypes;
DROP TABLE IF EXISTS Vehicles;
DROP TABLE IF EXISTS EmployeeCertifications;
DROP TABLE IF EXISTS EmployeeTrainingRecords;
DROP TABLE IF EXISTS EmployeeEquipmentQualifications;
DROP TABLE IF EXISTS Employees;
DROP TABLE IF EXISTS AccessRoles;
DROP TABLE IF EXISTS CertificationTypes;
DROP TABLE IF EXISTS TrainingTypes;
DROP TABLE IF EXISTS EquipmentQualifications;
DROP TABLE IF EXISTS Projects;
DROP TABLE IF EXISTS CustomerContacts;
DROP TABLE IF EXISTS Customers;
DROP TABLE IF EXISTS CustomerTypes;
DROP TABLE IF EXISTS ProjectStatuses;
DROP TABLE IF EXISTS ProjectTypes;
DROP TABLE IF EXISTS TaskStatuses;
DROP TABLE IF EXISTS ToolStatuses;
DROP TABLE IF EXISTS OrderStatuses;
DROP TABLE IF EXISTS VendorTypes;
DROP TABLE IF EXISTS raw_estimates; -- From App Core section
DROP TABLE IF EXISTS processed_estimates; -- From App Core section
DROP TABLE IF EXISTS wbs_elements; -- From App Core section
DROP TABLE IF EXISTS project_budgets; -- From App Core section
DROP TABLE IF EXISTS actual_costs; -- From App Core section
DROP TABLE IF EXISTS progress_updates; -- From App Core section
DROP TABLE IF EXISTS DailyLogObservations;
DROP TABLE IF EXISTS DailyLogMaterials;
DROP TABLE IF EXISTS DailyLogTasks;
DROP TABLE IF EXISTS DailyLogs;
DROP TABLE IF EXISTS MaterialLog; -- From App Core section
DROP TABLE IF EXISTS WBSElementResources; -- From App Core section


-- == Create Lookup Tables (Core Schema) ==
CREATE TABLE CustomerTypes (
    CustomerTypeID INTEGER PRIMARY KEY AUTOINCREMENT,
    TypeName TEXT(100) NOT NULL UNIQUE,
    Description TEXT(255) NULL
);
INSERT INTO CustomerTypes (TypeName, Description) VALUES
('Commercial', 'Standard Commercial Client'),
('Residential', 'Individual Residential Client'),
('General Contractor', 'Acts as GC'),
('Industrial', 'Industrial Facility Client');

CREATE TABLE ProjectStatuses (
    ProjectStatusID INTEGER PRIMARY KEY AUTOINCREMENT,
    StatusName TEXT(50) NOT NULL UNIQUE,
    Description TEXT(255) NULL
);
INSERT INTO ProjectStatuses (StatusName, Description) VALUES
('Prospect', 'Potential project, pre-bid'),
('Bidding', 'Currently in the bidding phase'),
('Awarded', 'Project awarded, pre-start'),
('Active', 'Project is currently in progress'),
('On Hold', 'Project is temporarily paused'),
('Completed', 'All work finished'),
('Cancelled', 'Project cancelled'),
('Warranty', 'Project complete, under warranty period'),
('Pending', 'Project created, awaiting further setup or activation');

CREATE TABLE ProjectTypes (
    ProjectTypeID INTEGER PRIMARY KEY AUTOINCREMENT,
    TypeName TEXT(100) NOT NULL UNIQUE,
    Description TEXT(255) NULL
);
INSERT INTO ProjectTypes (TypeName, Description) VALUES
('New Construction', 'Ground-up new building'),
('Tenant Improvement', 'Interior build-out or remodel'),
('Service Call', 'Minor repair or service work'),
('Design-Build', 'Project including design phase'),
('Infrastructure', 'Site work, utilities, etc.');

CREATE TABLE TaskStatuses (
    TaskStatusID INTEGER PRIMARY KEY AUTOINCREMENT,
    StatusName TEXT(50) NOT NULL UNIQUE,
    Description TEXT(255) NULL
);
INSERT INTO TaskStatuses (StatusName, Description) VALUES
('Pending', 'Task created, not yet started'),
('Assigned', 'Task assigned to resource(s)'),
('In Progress', 'Task is actively being worked on'),
('Blocked', 'Task progress is impeded'),
('Completed', 'Task finished'),
('Cancelled', 'Task will not be performed');

CREATE TABLE ToolStatuses (
    ToolStatusID INTEGER PRIMARY KEY AUTOINCREMENT,
    StatusName TEXT(50) NOT NULL UNIQUE,
    Description TEXT(255) NULL
);
INSERT INTO ToolStatuses (StatusName, Description) VALUES
('Available', 'In stock, ready for assignment'),
('Assigned', 'Checked out to a project or employee'),
('Damaged', 'Tool is damaged and needs repair'),
('Under Repair', 'Tool is currently being repaired'),
('Missing', 'Tool location unknown'),
('Retired', 'Tool removed from service');

CREATE TABLE OrderStatuses (
    OrderStatusID INTEGER PRIMARY KEY AUTOINCREMENT,
    StatusName TEXT(50) NOT NULL UNIQUE,
    AppliesToPO BOOLEAN NOT NULL DEFAULT 0,
    AppliesToSO BOOLEAN NOT NULL DEFAULT 0
);
INSERT INTO OrderStatuses (StatusName, AppliesToPO, AppliesToSO) VALUES
('Draft', 1, 1),('Submitted', 1, 1),('Approved', 1, 1),('Vendor Acknowledged', 1, 0),
('Partially Received', 1, 0),('Received', 1, 0),('Partially Shipped', 0, 1),
('Shipped', 0, 1),('Invoiced', 1, 1),('Paid', 1, 1),('Cancelled', 1, 1),('Closed', 1, 1);

CREATE TABLE VendorTypes (
    VendorTypeID INTEGER PRIMARY KEY AUTOINCREMENT,
    TypeName TEXT(100) NOT NULL UNIQUE,
    Description TEXT(255) NULL
);
INSERT INTO VendorTypes (TypeName, Description) VALUES
('Material Supplier', 'Provides electrical materials'),
('Subcontractor', 'Performs specific work packages'),
('Equipment Rental', 'Provides rental equipment'),
('Service Provider', 'Provides other services (e.g., IT, Accounting)');

CREATE TABLE LaborLevels (
    LaborLevelID INTEGER PRIMARY KEY AUTOINCREMENT,
    LevelName TEXT(100) NOT NULL UNIQUE,
    Description TEXT(255) NULL
);
INSERT INTO LaborLevels (LevelName, Description) VALUES
('Journeyman', 'Certified Electrician'),
('Apprentice', 'Apprentice Electrician'),
('Foreman', 'Lead Electrician on site'),
('Helper', 'General Labor Support');

CREATE TABLE TaskTags (
    TaskTagID INTEGER PRIMARY KEY AUTOINCREMENT,
    Tag TEXT(100) NOT NULL UNIQUE,
    Description TEXT(255) NULL
);
INSERT INTO TaskTags (Tag, Description) VALUES
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

-- == Create Core Tables ==
CREATE TABLE Vendors (
    VendorID INTEGER PRIMARY KEY AUTOINCREMENT,
    VendorName TEXT(255) NOT NULL UNIQUE,
    VendorTypeID INT NULL,
    ContactPerson TEXT(255) NULL,
    PhoneNumber TEXT(50) NULL,
    EmailAddress TEXT(255) NULL,
    Website TEXT(255) NULL,
    Address_Street TEXT(255) NULL,
    Address_City TEXT(100) NULL,
    Address_State TEXT(50) NULL,
    Address_ZipCode TEXT(20) NULL,
    AccountNumber TEXT(100) NULL,
    DefaultPaymentTerms TEXT(100) NULL,
    IsActive BOOLEAN NOT NULL DEFAULT 1,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_Vendors_VendorTypes FOREIGN KEY (VendorTypeID) REFERENCES VendorTypes(VendorTypeID)
);

CREATE TABLE Materials (
    MaterialSystemID INTEGER PRIMARY KEY AUTOINCREMENT,
    StockNumber TEXT(50) UNIQUE NOT NULL,
    MaterialName TEXT(255) NOT NULL,
    Description TEXT(500) NULL,
    ExtendedDescription TEXT(1000) NULL,
    Manufacturer TEXT(100) NULL,
    ManufacturerPartNumber TEXT(100) NULL,
    PartNumber TEXT(100) NULL,
    Barcode TEXT(100) NULL,
    UnitOfMeasure TEXT(20) NOT NULL,
    DefaultCost REAL NULL,
    DefaultPrice REAL NULL,
    Category TEXT(100) NULL,
    SubCategory TEXT(100) NULL,
    PreferredVendorID INTEGER NULL,
    QuantityOnHand REAL NULL DEFAULT 0,
    ReorderPoint REAL NULL,
    SalesTaxCode TEXT(50) NULL,
    Labor1 REAL NULL,
    Labor2 REAL NULL,
    Labor3 REAL NULL,
    IsInventoried BOOLEAN NOT NULL DEFAULT 0,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (PreferredVendorID) REFERENCES Vendors(VendorID) ON DELETE SET NULL
);
CREATE INDEX IX_Materials_StockNumber ON Materials (StockNumber);
CREATE INDEX IX_Materials_Barcode ON Materials (Barcode);
CREATE INDEX IX_Materials_MaterialName ON Materials (MaterialName);
CREATE INDEX IX_Materials_PartNumber ON Materials (PartNumber);
CREATE INDEX IX_Materials_ManufacturerPartNumber ON Materials (ManufacturerPartNumber);
CREATE INDEX IX_Materials_Category ON Materials (Category);
CREATE INDEX IX_Materials_SubCategory ON Materials (SubCategory);

CREATE TABLE IF NOT EXISTS Assemblies (
    AssemblyID INTEGER PRIMARY KEY AUTOINCREMENT,
    AssemblyItemNumber TEXT UNIQUE NOT NULL,
    AssemblyName TEXT NOT NULL,
    Description TEXT NULL,
    Phase TEXT NULL,
    TotalEstMaterialCost REAL NULL,
    TotalEstLaborHours REAL NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS IX_Assemblies_AssemblyItemNumber ON Assemblies (AssemblyItemNumber);
CREATE INDEX IF NOT EXISTS IX_Assemblies_AssemblyName ON Assemblies (AssemblyName);

CREATE TABLE IF NOT EXISTS AssemblyComponents (
    AssemblyComponentID INTEGER PRIMARY KEY AUTOINCREMENT,
    AssemblyID INTEGER NOT NULL,
    MaterialStockNumber TEXT NOT NULL,
    QuantityInAssembly REAL NOT NULL,
    UnitOfMeasure TEXT NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (AssemblyID) REFERENCES Assemblies(AssemblyID) ON DELETE CASCADE,
    FOREIGN KEY (MaterialStockNumber) REFERENCES Materials(StockNumber) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS IX_AssemblyComponents_AssemblyID ON AssemblyComponents (AssemblyID);
CREATE INDEX IF NOT EXISTS IX_AssemblyComponents_MaterialStockNumber ON AssemblyComponents (MaterialStockNumber);

CREATE TABLE ToolTypes (
    ToolTypeID INTEGER PRIMARY KEY AUTOINCREMENT,
    TypeName TEXT(150) NOT NULL UNIQUE,
    Category TEXT(100) NULL,
    DefaultItemNumber TEXT(100) NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IX_ToolTypes_DefaultItemNumber ON ToolTypes (DefaultItemNumber);

CREATE TABLE Tools (
    ToolID INTEGER PRIMARY KEY AUTOINCREMENT,
    ToolTypeID INT NULL,
    ToolSpecificMarking TEXT(100) NOT NULL UNIQUE,
    ItemNumber TEXT(100) NULL,
    ToolStatusID INT NULL,
    PurchaseDate TEXT NULL,
    PurchasePrice DECIMAL(10, 2) NULL,
    CurrentCondition TEXT(100) NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_Tools_ToolTypes FOREIGN KEY (ToolTypeID) REFERENCES ToolTypes(ToolTypeID),
    CONSTRAINT FK_Tools_ToolStatuses FOREIGN KEY (ToolStatusID) REFERENCES ToolStatuses(ToolStatusID)
);
CREATE INDEX IX_Tools_ItemNumber ON Tools (ItemNumber);
CREATE INDEX IX_Tools_ToolStatusID ON Tools (ToolStatusID);

CREATE TABLE Vehicles (
    VehicleID INTEGER PRIMARY KEY AUTOINCREMENT,
    VehicleName TEXT(100) NOT NULL UNIQUE,
    VehicleType TEXT(50) NOT NULL,
    LicensePlate TEXT(20) NULL UNIQUE,
    VIN TEXT(17) NULL UNIQUE,
    Make TEXT(100) NULL,
    Model TEXT(100) NULL,
    Year INT NULL,
    Status TEXT(50) NOT NULL DEFAULT 'Available',
    DateAcquired TEXT NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- == Create HR Tables ==
CREATE TABLE AccessRoles (
    AccessRoleID INTEGER PRIMARY KEY AUTOINCREMENT,
    RoleName TEXT(100) NOT NULL UNIQUE,
    Description TEXT(500) NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO AccessRoles (RoleName, Description) VALUES
('Administrator', 'Full system access'),('Project Manager', 'Manages projects, estimates, financials'),
('Foreman', 'Manages field tasks, time entries, assignments'),('Electrician', 'Standard field employee access'),
('Office Staff', 'Access to administrative functions');

CREATE TABLE Employees (
    EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT,
    FirstName TEXT(100) NOT NULL, LastName TEXT(100) NOT NULL, Title TEXT(100) NULL,
    DepartmentArea TEXT(100) NULL, ReportsToEmployeeID INT NULL, Duties TEXT NULL, Notes TEXT NULL,
    Position TEXT(100) NULL, Strata TEXT(50) NULL, Band TEXT(50) NULL,
    SalaryLow DECIMAL(18, 2) NULL, SalaryHigh DECIMAL(18, 2) NULL,
    PhoneNumber TEXT(50) NULL, WorkEmail TEXT(255) NULL UNIQUE, ExakTimeID TEXT(100) NULL UNIQUE,
    IsActive BOOLEAN NOT NULL DEFAULT 1, HireDate TEXT NULL, AccessRoleID INT NULL,
    EmployeeCity TEXT(100) NULL, MainEmail TEXT(255) NULL, MainPhoneNumber TEXT(50) NULL,
    PayrollDriverInfo TEXT(255) NULL, PerformanceEvalDueDate TEXT NULL, ShirtSize TEXT(20) NULL,
    Card2025Info TEXT(100) NULL, EducationBackground TEXT(500) NULL, ForemanStartDate TEXT NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_Employees_ReportsTo FOREIGN KEY (ReportsToEmployeeID) REFERENCES Employees(EmployeeID) ON DELETE NO ACTION,
    CONSTRAINT FK_Employees_AccessRoles FOREIGN KEY (AccessRoleID) REFERENCES AccessRoles(AccessRoleID)
);
CREATE INDEX IX_Employees_ReportsToEmployeeID ON Employees (ReportsToEmployeeID);

CREATE TABLE CertificationTypes (
    CertificationTypeID INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT(150) NOT NULL UNIQUE, Description TEXT(500) NULL
);
INSERT INTO CertificationTypes (Name, Description) VALUES
('Electrical License', 'State or Local Electrical License'),('OSHA 10', 'OSHA 10 Hour Certification'),
('OSHA 30', 'OSHA 30 Hour Certification'),('First Aid/CPR', 'First Aid and CPR Certification'),
('BICSI Installer', 'BICSI Installation Certification'),('BICSI Technician', 'BICSI Technician Certification'),
('BICSI RCDD', 'BICSI Registered Communications Distribution Designer');

CREATE TABLE EmployeeCertifications (
    EmployeeCertificationID INTEGER PRIMARY KEY AUTOINCREMENT, EmployeeID INT NOT NULL, CertificationTypeID INT NOT NULL,
    IssueDate TEXT NULL, ExpiryDate TEXT NULL, CertificationNumber TEXT(100) NULL, Details TEXT(255) NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_EmployeeCertifications_Employees FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID) ON DELETE CASCADE,
    CONSTRAINT FK_EmployeeCertifications_CertificationTypes FOREIGN KEY (CertificationTypeID) REFERENCES CertificationTypes(CertificationTypeID),
    CONSTRAINT UK_Employee_CertificationType UNIQUE (EmployeeID, CertificationTypeID)
);
CREATE INDEX IX_EmployeeCertifications_ExpiryDate ON EmployeeCertifications (ExpiryDate);

CREATE TABLE TrainingTypes (
    TrainingTypeID INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT(150) NOT NULL UNIQUE,
    IsPolicyAcknowledgement BOOLEAN NOT NULL DEFAULT 0, Description TEXT(500) NULL
);
INSERT INTO TrainingTypes (Name, IsPolicyAcknowledgement, Description) VALUES
('Arc Flash PPE Policy Signed', 1, 'Acknowledgement of Arc Flash PPE Policy'),
('Open Trench Policy Signed', 1, 'Acknowledgement of Open Trench / Excavation Policy'),
('Elevated Surfaces Policy Signed', 1, 'Acknowledgement of Elevated Surfaces / Fall Protection Policy'),
('Driving Policy & Video Completed', 1, 'Acknowledgement of Driving Policy and Watched Safety Video'),
('Arc Flash PPE Competent Person', 0, 'Training for Arc Flash Competent Person'),
('Open Trench Competent Person', 0, 'Training for Open Trench / Excavation Competent Person'),
('Fall Protection Trained', 0, 'General Fall Protection Training'),
('Hazard Communication Trained', 0, 'Training on Hazard Communication Standards (HazCom)'),
('Respiratory Protection Trained', 0, 'Training on Respiratory Protection Equipment and Use'),
('Scaffolding Trained', 0, 'Training on Safe Scaffold Use'),('Ladder Trained', 0, 'Training on Safe Ladder Use'),
('Lockout/Tagout Trained', 0, 'Training on Lockout/Tagout Procedures (LOTO)'),
('Power Industrial Truck Trained', 0, 'Training for Powered Industrial Trucks (e.g., Forklifts - general)'),
('PPE Eye & Face Protection Trained', 0, 'Training on Eye and Face Protection PPE'),
('Machine Guarding Trained', 0, 'Training on Machine Guarding Safety'),
('Little Giant Ladder Trained', 0, 'Specific training for Little Giant Ladders');

CREATE TABLE EmployeeTrainingRecords (
    EmployeeTrainingRecordID INTEGER PRIMARY KEY AUTOINCREMENT, EmployeeID INT NOT NULL, TrainingTypeID INT NOT NULL,
    CompletionDate TEXT NOT NULL, ExpiryDate TEXT NULL, Trainer TEXT(150) NULL, Notes TEXT(500) NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_EmployeeTrainingRecords_Employees FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID) ON DELETE CASCADE,
    CONSTRAINT FK_EmployeeTrainingRecords_TrainingTypes FOREIGN KEY (TrainingTypeID) REFERENCES TrainingTypes(TrainingTypeID),
    CONSTRAINT UK_Employee_TrainingType_Completion UNIQUE (EmployeeID, TrainingTypeID, CompletionDate)
);
CREATE INDEX IX_EmployeeTrainingRecords_ExpiryDate ON EmployeeTrainingRecords (ExpiryDate);

CREATE TABLE EquipmentQualifications (
    EquipmentQualificationID INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT(100) NOT NULL UNIQUE, Description TEXT(500) NULL
);
INSERT INTO EquipmentQualifications (Name, Description) VALUES
('Forklift', 'Standard Warehouse Forklift'),('Scissor Lift', 'Aerial Work Platform - Scissor Type'),
('Jackhammer', 'Pneumatic or Electric Jackhammer Operation'),('Tugger', 'Material Handling Tugger Vehicle'),
('LULL', 'Extended Reach Forklift / Telehandler (Lull is a brand name)'),('Core Drill', 'Concrete Core Drilling Equipment'),
('Mini Excavator', 'Small Excavator Operation'),('Backhoe', 'Backhoe Loader Operation'),
('Skid Steer', 'Skid Steer Loader Operation'),('Cherry Picker', 'Aerial Work Platform - Boom Type (Often Vehicle Mounted)'),
('Man Lift', 'Aerial Work Platform - Articulated or Telescopic Boom Lift'),('Boom Forklift', 'Telehandler / Extended Reach Forklift'),
('Trencher', 'Mechanical Trencher Operation');

CREATE TABLE EmployeeEquipmentQualifications (
    EmployeeEquipmentQualificationID INTEGER PRIMARY KEY AUTOINCREMENT, EmployeeID INT NOT NULL, EquipmentQualificationID INT NOT NULL,
    QualificationDate TEXT NOT NULL, QualifiedByEmployeeID INT NULL, Notes TEXT(500) NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_EmployeeEquipmentQualifications_Employees FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID) ON DELETE CASCADE,
    CONSTRAINT FK_EmployeeEquipmentQualifications_EquipmentQualifications FOREIGN KEY (EquipmentQualificationID) REFERENCES EquipmentQualifications(EquipmentQualificationID),
    CONSTRAINT FK_EmployeeEquipmentQualifications_QualifiedBy FOREIGN KEY (QualifiedByEmployeeID) REFERENCES Employees(EmployeeID),
    CONSTRAINT UK_Employee_EquipmentQualification UNIQUE (EmployeeID, EquipmentQualificationID)
);

-- == Create Sales Tables ==
CREATE TABLE Customers (
    CustomerID INTEGER PRIMARY KEY AUTOINCREMENT, CustomerName TEXT(255) NOT NULL, CustomerTypeID INT NULL,
    BillingAddress_Street TEXT(255) NULL, BillingAddress_City TEXT(100) NULL,
    BillingAddress_State TEXT(50) NULL, BillingAddress_ZipCode TEXT(20) NULL,
    QuickBooksCustomerID TEXT(100) NULL UNIQUE, DefaultPaymentTerms TEXT(100) NULL,
    IsActive BOOLEAN NOT NULL DEFAULT 1, DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_Customers_CustomerTypes FOREIGN KEY (CustomerTypeID) REFERENCES CustomerTypes(CustomerTypeID)
);

CREATE TABLE CustomerContacts (
    ContactID INTEGER PRIMARY KEY AUTOINCREMENT, CustomerID INT NOT NULL, FirstName TEXT(100) NOT NULL,
    LastName TEXT(100) NULL, Title TEXT(100) NULL, PhoneNumber TEXT(50) NULL, MobileNumber TEXT(50) NULL,
    EmailAddress TEXT(255) NULL, IsPrimaryContact BOOLEAN NOT NULL DEFAULT 0, Notes TEXT(500) NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_CustomerContacts_Customers FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID) ON DELETE CASCADE
);
CREATE INDEX IX_CustomerContacts_CustomerID ON CustomerContacts (CustomerID);
CREATE INDEX IX_CustomerContacts_EmailAddress ON CustomerContacts (EmailAddress);

CREATE TABLE SalesOrders (
    SalesOrderID INTEGER PRIMARY KEY AUTOINCREMENT, CustomerID INT NOT NULL, ProjectID INT NULL,
    SalesOrderNumber TEXT(100) NOT NULL UNIQUE, CustomerPONumber TEXT(100) NULL, OrderDate TEXT NOT NULL,
    EmployeeID_Salesperson INT NULL, OrderStatusID INT NULL, Description TEXT(1000) NULL,
    Subtotal DECIMAL(18, 2) NULL, TaxAmount DECIMAL(18, 2) NULL, TotalAmount DECIMAL(18, 2) NULL,
    Notes TEXT NULL, DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_SalesOrders_Customers FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    CONSTRAINT FK_SalesOrders_Salesperson FOREIGN KEY (EmployeeID_Salesperson) REFERENCES Employees(EmployeeID),
    CONSTRAINT FK_SalesOrders_OrderStatuses FOREIGN KEY (OrderStatusID) REFERENCES OrderStatuses(OrderStatusID),
    CONSTRAINT FK_SalesOrders_Projects FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) -- Added
);
CREATE INDEX IX_SalesOrders_CustomerID ON SalesOrders (CustomerID);
CREATE INDEX IX_SalesOrders_ProjectID ON SalesOrders (ProjectID);
CREATE INDEX IX_SalesOrders_OrderStatusID ON SalesOrders (OrderStatusID);

CREATE TABLE SalesOrderLineItems (
    SOLineItemID INTEGER PRIMARY KEY AUTOINCREMENT, SalesOrderID INT NOT NULL, LineNumber INT NOT NULL,
    MaterialID INT NULL, ServiceID INT NULL, Description TEXT(500) NOT NULL,
    Quantity DECIMAL(18, 4) NOT NULL, UnitOfMeasure TEXT(20) NOT NULL, UnitPrice DECIMAL(18, 4) NOT NULL,
    LineTotal DECIMAL(18, 2) NULL, Notes TEXT(500) NULL,
    CONSTRAINT FK_SalesOrderLineItems_SalesOrders FOREIGN KEY (SalesOrderID) REFERENCES SalesOrders(SalesOrderID) ON DELETE CASCADE,
    CONSTRAINT FK_SalesOrderLineItems_Materials FOREIGN KEY (MaterialID) REFERENCES Materials(MaterialSystemID),
    CONSTRAINT UK_SalesOrderLineItems_Line UNIQUE (SalesOrderID, LineNumber)
);
CREATE INDEX IX_SalesOrderLineItems_MaterialID ON SalesOrderLineItems (MaterialID);

CREATE TABLE EstimateHeaders (
    EstimateHeaderID INTEGER PRIMARY KEY AUTOINCREMENT, EstimateNumber TEXT(100) NOT NULL UNIQUE, ProjectID INT NULL,
    CustomerID INT NOT NULL, EstimateDate TEXT NOT NULL, ExpiryDate TEXT NULL, EmployeeID_Estimator INT NULL,
    Status TEXT(50) NULL, Description TEXT(1000) NULL, Subtotal DECIMAL(18, 2) NULL, TaxAmount DECIMAL(18, 2) NULL,
    TotalAmount DECIMAL(18, 2) NULL, Notes TEXT NULL, DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_EstimateHeaders_Customers FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    CONSTRAINT FK_EstimateHeaders_Estimator FOREIGN KEY (EmployeeID_Estimator) REFERENCES Employees(EmployeeID),
    CONSTRAINT FK_EstimateHeaders_Projects FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) -- Added
);
CREATE INDEX IX_EstimateHeaders_ProjectID ON EstimateHeaders (ProjectID);
CREATE INDEX IX_EstimateHeaders_CustomerID ON EstimateHeaders (CustomerID);

CREATE TABLE EstimateLineItems (
    EstimateLineItemID INTEGER PRIMARY KEY AUTOINCREMENT, EstimateHeaderID INT NOT NULL, LineNumber INT NOT NULL,
    MaterialID INT NULL, ServiceID INT NULL, Description TEXT(500) NOT NULL,
    Quantity DECIMAL(18, 4) NOT NULL, UnitOfMeasure TEXT(20) NOT NULL, UnitCost DECIMAL(18, 4) NULL,
    UnitPrice DECIMAL(18, 4) NOT NULL, LineTotal DECIMAL(18, 2) NULL, Notes TEXT(500) NULL,
    CONSTRAINT FK_EstimateLineItems_EstimateHeaders FOREIGN KEY (EstimateHeaderID) REFERENCES EstimateHeaders(EstimateHeaderID) ON DELETE CASCADE,
    CONSTRAINT FK_EstimateLineItems_Materials FOREIGN KEY (MaterialID) REFERENCES Materials(MaterialSystemID),
    CONSTRAINT UK_EstimateLineItems_Line UNIQUE (EstimateHeaderID, LineNumber)
);
CREATE INDEX IX_EstimateLineItems_MaterialID ON EstimateLineItems (MaterialID);

-- == Create Purchasing Tables ==
CREATE TABLE PurchaseOrders (
    PurchaseOrderID INTEGER PRIMARY KEY AUTOINCREMENT, VendorID INT NOT NULL, ProjectID INT NULL,
    EmployeeID_Requester INT NULL, EmployeeID_Approver INT NULL, PONumber TEXT(100) NOT NULL UNIQUE,
    VendorOrderNumber TEXT(100) NULL, OrderDate TEXT NOT NULL, ExpectedDeliveryDate TEXT NULL, ActualDeliveryDate TEXT NULL,
    ShippingAddress_Street TEXT(255) NULL, ShippingAddress_City TEXT(100) NULL,
    ShippingAddress_State TEXT(50) NULL, ShippingAddress_ZipCode TEXT(20) NULL, ShippingInstructions TEXT(500) NULL,
    OrderStatusID INT NULL, Subtotal DECIMAL(18, 2) NULL, TaxAmount DECIMAL(18, 2) NULL, ShippingCost DECIMAL(18, 2) NULL,
    TotalAmount DECIMAL(18, 2) NULL, Notes TEXT NULL, DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_PurchaseOrders_Vendors FOREIGN KEY (VendorID) REFERENCES Vendors(VendorID),
    CONSTRAINT FK_PurchaseOrders_Requester FOREIGN KEY (EmployeeID_Requester) REFERENCES Employees(EmployeeID),
    CONSTRAINT FK_PurchaseOrders_Approver FOREIGN KEY (EmployeeID_Approver) REFERENCES Employees(EmployeeID),
    CONSTRAINT FK_PurchaseOrders_OrderStatuses FOREIGN KEY (OrderStatusID) REFERENCES OrderStatuses(OrderStatusID),
    CONSTRAINT FK_PurchaseOrders_Projects FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) -- Added
);
CREATE INDEX IX_PurchaseOrders_VendorID ON PurchaseOrders (VendorID);
CREATE INDEX IX_PurchaseOrders_ProjectID ON PurchaseOrders (ProjectID);
CREATE INDEX IX_PurchaseOrders_OrderStatusID ON PurchaseOrders (OrderStatusID);

CREATE TABLE PurchaseOrderLineItems (
    POLineItemID INTEGER PRIMARY KEY AUTOINCREMENT, PurchaseOrderID INT NOT NULL, LineNumber INT NOT NULL,
    MaterialID INT NULL, Description TEXT(500) NOT NULL, QuantityOrdered DECIMAL(18, 4) NOT NULL,
    UnitOfMeasure TEXT(20) NOT NULL, UnitPrice DECIMAL(18, 4) NOT NULL, LineTotal DECIMAL(18, 2) NULL,
    QuantityReceived DECIMAL(18, 4) NULL DEFAULT 0, DateLastReceived TEXT NULL, Notes TEXT(500) NULL,
    CONSTRAINT FK_PurchaseOrderLineItems_PurchaseOrders FOREIGN KEY (PurchaseOrderID) REFERENCES PurchaseOrders(PurchaseOrderID) ON DELETE CASCADE,
    CONSTRAINT FK_PurchaseOrderLineItems_Materials FOREIGN KEY (MaterialID) REFERENCES Materials(MaterialSystemID),
    CONSTRAINT UK_PurchaseOrderLineItems_Line UNIQUE (PurchaseOrderID, LineNumber)
);
CREATE INDEX IX_PurchaseOrderLineItems_MaterialID ON PurchaseOrderLineItems (MaterialID);

-- == Create Projects Tables ==
CREATE TABLE Projects (
    ProjectID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectName TEXT(255) NOT NULL, CustomerID INT NOT NULL,
    ProjectNumber TEXT(100) NULL UNIQUE, Location_Street TEXT(255) NULL, Location_City TEXT(100) NULL,
    Location_State TEXT(50) NULL, Location_ZipCode TEXT(20) NULL, ProjectStatusID INT NULL, ProjectTypeID INT NULL,
    StartDate TEXT NULL, EndDate TEXT NULL, ProjectManagerEmployeeID INT NULL, ForemanEmployeeID INT NULL,
    ContractAmount DECIMAL(18, 2) NULL, SquareFootage DECIMAL(10, 2) NULL, IncludesSiteWork BOOLEAN NULL,
    BidDueDate TEXT NULL, BidPurpose TEXT(255) NULL, DeliveryMethod TEXT(100) NULL, IsTaxExempt BOOLEAN NULL,
    IsBondRequired BOOLEAN NULL, CCIP_OCIP_Flag TEXT(50) NULL, EstimatedCost DECIMAL(18, 2) NULL,
    EstimatedManHours DECIMAL(10, 2) NULL, EstimatedDuration DECIMAL(10, 2) NULL, DurationDays INTEGER NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_Projects_Customers FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    CONSTRAINT FK_Projects_ProjectManager FOREIGN KEY (ProjectManagerEmployeeID) REFERENCES Employees(EmployeeID),
    CONSTRAINT FK_Projects_Foreman FOREIGN KEY (ForemanEmployeeID) REFERENCES Employees(EmployeeID),
    CONSTRAINT FK_Projects_ProjectStatuses FOREIGN KEY (ProjectStatusID) REFERENCES ProjectStatuses(ProjectStatusID),
    CONSTRAINT FK_Projects_ProjectTypes FOREIGN KEY (ProjectTypeID) REFERENCES ProjectTypes(ProjectTypeID)
);
CREATE INDEX IX_Projects_CustomerID ON Projects (CustomerID);
CREATE INDEX IX_Projects_ProjectNumber ON Projects (ProjectNumber);
CREATE INDEX IX_Projects_ProjectStatusID ON Projects (ProjectStatusID);
CREATE INDEX IX_Projects_ProjectManagerEmployeeID ON Projects (ProjectManagerEmployeeID);
CREATE INDEX IX_Projects_ForemanEmployeeID ON Projects (ForemanEmployeeID);

CREATE TABLE Tasks (
    TaskID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INT NOT NULL, WBSElementID INT NULL, TaskType TEXT(100) NOT NULL, Description TEXT NOT NULL,
    Phase TEXT NULL, ScheduledStartDate TEXT NULL, ScheduledEndDate TEXT NULL, ActualStartDate TEXT NULL, ActualEndDate TEXT NULL,
    EstimatedHours REAL NULL, ActualHours REAL NULL, PercentComplete REAL NULL DEFAULT 0.0, TaskStatusID INT NULL,
    Priority INT NULL, LeadEmployeeID INT NULL, CreatedByEmployeeID INT NULL, PredecessorTaskID INT NULL, Notes TEXT NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_Tasks_Projects FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
    CONSTRAINT FK_Tasks_WBSElements FOREIGN KEY (WBSElementID) REFERENCES wbs_elements(WBSElementID) ON DELETE SET NULL, -- Added FK to wbs_elements
    CONSTRAINT FK_Tasks_CreatedByEmployee FOREIGN KEY (CreatedByEmployeeID) REFERENCES Employees(EmployeeID) ON DELETE SET NULL,
    CONSTRAINT FK_Tasks_LeadEmployee FOREIGN KEY (LeadEmployeeID) REFERENCES Employees(EmployeeID) ON DELETE SET NULL,
    CONSTRAINT FK_Tasks_TaskStatuses FOREIGN KEY (TaskStatusID) REFERENCES TaskStatuses(TaskStatusID),
    CONSTRAINT FK_Tasks_PredecessorTask FOREIGN KEY (PredecessorTaskID) REFERENCES Tasks(TaskID) ON DELETE SET NULL
);
CREATE INDEX IX_Tasks_ProjectID ON Tasks (ProjectID);
CREATE INDEX IX_Tasks_WBSElementID ON Tasks (WBSElementID); -- Added index
CREATE INDEX IX_Tasks_TaskStatusID ON Tasks (TaskStatusID);
CREATE INDEX IX_Tasks_PredecessorTaskID ON Tasks (PredecessorTaskID);
CREATE INDEX IX_Tasks_LeadEmployeeID ON Tasks (LeadEmployeeID);

CREATE TABLE ResourceAssignments (
    AssignmentID INTEGER PRIMARY KEY AUTOINCREMENT, TaskID INT NOT NULL, EmployeeID INT NOT NULL, VehicleID INT NULL,
    AssignedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, AssignmentStartDate TEXT NULL, AssignmentEndDate TEXT NULL,
    Notes TEXT(500) NULL, DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_ResourceAssignments_Tasks FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID) ON DELETE CASCADE,
    CONSTRAINT FK_ResourceAssignments_Employees FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID),
    CONSTRAINT FK_ResourceAssignments_Vehicles FOREIGN KEY (VehicleID) REFERENCES Vehicles(VehicleID),
    CONSTRAINT UK_ResourceAssignments_Task_Employee UNIQUE (TaskID, EmployeeID)
);
CREATE INDEX IX_ResourceAssignments_EmployeeID ON ResourceAssignments (EmployeeID);
CREATE INDEX IX_ResourceAssignments_VehicleID ON ResourceAssignments (VehicleID);

CREATE TABLE ToolAssignments (
    ToolAssignmentID INTEGER PRIMARY KEY AUTOINCREMENT, ToolID INT NOT NULL, ProjectID INT NULL,
    AssignedToEmployeeID INT NULL, AssignedByEmployeeID INT NULL, TaskID INT NULL,
    DateAssigned TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, ExpectedReturnDate TEXT NULL, DateReturned TEXT NULL,
    ReturnedByEmployeeID INT NULL, ConditionOut TEXT(100) NULL, ConditionIn TEXT(100) NULL, Notes TEXT NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_ToolAssignments_Tools FOREIGN KEY (ToolID) REFERENCES Tools(ToolID),
    CONSTRAINT FK_ToolAssignments_Projects FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID),
    CONSTRAINT FK_ToolAssignments_Tasks FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID),
    CONSTRAINT FK_ToolAssignments_AssignedToEmployee FOREIGN KEY (AssignedToEmployeeID) REFERENCES Employees(EmployeeID),
    CONSTRAINT FK_ToolAssignments_AssignedByEmployee FOREIGN KEY (AssignedByEmployeeID) REFERENCES Employees(EmployeeID),
    CONSTRAINT FK_ToolAssignments_ReturnedByEmployee FOREIGN KEY (ReturnedByEmployeeID) REFERENCES Employees(EmployeeID)
);
CREATE INDEX IX_ToolAssignments_ToolID_DateReturned ON ToolAssignments (ToolID) WHERE DateReturned IS NULL;
CREATE INDEX IX_ToolAssignments_ProjectID ON ToolAssignments (ProjectID);
CREATE INDEX IX_ToolAssignments_AssignedToEmployeeID ON ToolAssignments (AssignedToEmployeeID);
CREATE INDEX IX_ToolAssignments_TaskID ON ToolAssignments (TaskID);

CREATE TABLE ProjectDocuments (
    ProjectDocumentID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INT NOT NULL, DocumentName TEXT(255) NOT NULL,
    DocumentType TEXT(100) NULL, FilePath TEXT(1000) NOT NULL, UploadedByEmployeeID INT NULL,
    UploadDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, Description TEXT NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_ProjectDocuments_Projects FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
    CONSTRAINT FK_ProjectDocuments_UploadedBy FOREIGN KEY (UploadedByEmployeeID) REFERENCES Employees(EmployeeID)
);
CREATE INDEX IX_ProjectDocuments_ProjectID ON ProjectDocuments (ProjectID);

CREATE TABLE ChangeOrders (
    ChangeOrderID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INT NOT NULL, ChangeOrderNumber TEXT(100) NOT NULL,
    Description TEXT NOT NULL, Status TEXT(50) NOT NULL, RequestDate TEXT NULL, ApprovalDate TEXT NULL,
    Amount DECIMAL(18, 2) NOT NULL DEFAULT 0, CreatedByEmployeeID INT NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_ChangeOrders_Projects FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
    CONSTRAINT FK_ChangeOrders_CreatedBy FOREIGN KEY (CreatedByEmployeeID) REFERENCES Employees(EmployeeID),
    CONSTRAINT UK_ChangeOrders_Project_Number UNIQUE (ProjectID, ChangeOrderNumber)
);
CREATE INDEX IX_ChangeOrders_Status ON ChangeOrders (Status);

CREATE TABLE ChangeOrderLineItems (
    ChangeOrderLineItemID INTEGER PRIMARY KEY AUTOINCREMENT, ChangeOrderID INT NOT NULL, LineNumber INT NOT NULL,
    Description TEXT(500) NOT NULL, MaterialID INT NULL, ServiceID INT NULL, Quantity DECIMAL(18, 4) NULL,
    UnitOfMeasure TEXT(20) NULL, UnitPrice DECIMAL(18, 4) NULL, LineTotal DECIMAL(18, 2) NULL, Notes TEXT(500) NULL,
    CONSTRAINT FK_ChangeOrderLineItems_ChangeOrders FOREIGN KEY (ChangeOrderID) REFERENCES ChangeOrders(ChangeOrderID) ON DELETE CASCADE,
    CONSTRAINT FK_ChangeOrderLineItems_Materials FOREIGN KEY (MaterialID) REFERENCES Materials(MaterialSystemID),
    CONSTRAINT UK_ChangeOrderLineItems_Line UNIQUE (ChangeOrderID, LineNumber)
);

-- == Create Shipping Table ==
CREATE TABLE ShipmentManifestItems (
    ShipmentManifestItemID INTEGER PRIMARY KEY AUTOINCREMENT, TaskID INT NOT NULL, ProjectID INT NULL,
    MaterialID INT NULL, ToolID INT NULL, QuantityShipped DECIMAL(18, 4) NOT NULL, UnitOfMeasure TEXT(20) NULL,
    ShipmentDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, ShippedByEmployeeID INT NULL, Notes TEXT(500) NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_ShipmentManifestItems_Tasks FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID),
    CONSTRAINT FK_ShipmentManifestItems_Materials FOREIGN KEY (MaterialID) REFERENCES Materials(MaterialSystemID),
    CONSTRAINT FK_ShipmentManifestItems_Tools FOREIGN KEY (ToolID) REFERENCES Tools(ToolID),
    CONSTRAINT FK_ShipmentManifestItems_ShippedBy FOREIGN KEY (ShippedByEmployeeID) REFERENCES Employees(EmployeeID),
    CONSTRAINT CK_ShipmentManifestItems_MaterialOrTool CHECK ((MaterialID IS NOT NULL AND ToolID IS NULL) OR (MaterialID IS NULL AND ToolID IS NOT NULL))
);
CREATE INDEX IX_ShipmentManifestItems_TaskID ON ShipmentManifestItems (TaskID);
CREATE INDEX IX_ShipmentManifestItems_MaterialID ON ShipmentManifestItems (MaterialID);
CREATE INDEX IX_ShipmentManifestItems_ToolID ON ShipmentManifestItems (ToolID);

-- == Create Time Tracking Table ==
CREATE TABLE TimeEntries (
    TimeEntryID INTEGER PRIMARY KEY AUTOINCREMENT, EmployeeID INT NOT NULL, ProjectID INT NOT NULL, TaskID INT NULL,
    EntryDate TEXT NOT NULL, HoursWorked DECIMAL(5, 2) NOT NULL, TimeCode TEXT(50) NULL, CostCode TEXT(50) NULL,
    Notes TEXT(500) NULL, IsApproved BOOLEAN NOT NULL DEFAULT 0, ApprovedByEmployeeID INT NULL, ApprovalDate TEXT NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_TimeEntries_Employees FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID),
    CONSTRAINT FK_TimeEntries_Projects FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID),
    CONSTRAINT FK_TimeEntries_Tasks FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID),
    CONSTRAINT FK_TimeEntries_ApprovedBy FOREIGN KEY (ApprovedByEmployeeID) REFERENCES Employees(EmployeeID),
    CONSTRAINT CK_TimeEntries_HoursWorked CHECK (HoursWorked > 0 AND HoursWorked <= 24)
);
CREATE INDEX IX_TimeEntries_Employee_Date ON TimeEntries (EmployeeID, EntryDate);
CREATE INDEX IX_TimeEntries_Project_Date ON TimeEntries (ProjectID, EntryDate);
CREATE INDEX IX_TimeEntries_TaskID ON TimeEntries (TaskID);

-- ========================================================================== --
--                           SCRIPT COMPLETE                                  --
-- ========================================================================== --

-- == Application Core Tables (as per README) ==
-- These tables support the primary workflow of the application modules.
-- Note: Some of these tables (Projects, Tasks, Materials, Vendors) are already defined above
-- in the "Davis Electric ERD" section with more detail.
-- The definitions below are simpler and might be from an earlier version or for specific app logic.
-- This duplication needs to be resolved. For now, assuming the more detailed ERD versions are primary.
-- The `IF NOT EXISTS` clause will prevent errors if they are already created.

-- Raw Estimates (Data ingested from CSV/Excel)
CREATE TABLE IF NOT EXISTS raw_estimates (
    RawEstimateID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INT NULL, RawData TEXT NOT NULL,
    SourceFile TEXT NULL, ImportDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, Status TEXT DEFAULT 'Pending Processing',
    CONSTRAINT FK_RawEstimates_Projects FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS IX_RawEstimates_ProjectID ON raw_estimates (ProjectID);

-- Processed Estimates (Cleaned and standardized estimate data)
CREATE TABLE IF NOT EXISTS processed_estimates (
    ProcessedEstimateID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INT NULL, RawEstimateID INT NULL,
    CostCode TEXT NULL, Description TEXT NOT NULL, Quantity REAL NULL, Unit TEXT NULL, UnitCost REAL NULL,
    TotalCost REAL NULL, Phase TEXT NULL, ProcessedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_ProcessedEstimates_Projects FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE SET NULL,
    CONSTRAINT FK_ProcessedEstimates_RawEstimates FOREIGN KEY (RawEstimateID) REFERENCES raw_estimates(RawEstimateID) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS IX_ProcessedEstimates_ProjectID ON processed_estimates (ProjectID);
CREATE INDEX IF NOT EXISTS IX_ProcessedEstimates_RawEstimateID ON processed_estimates (RawEstimateID);

-- WBS Elements (Work Breakdown Structure)
CREATE TABLE IF NOT EXISTS wbs_elements (
    WBSElementID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INT NOT NULL, ProcessedEstimateID INT NULL,
    ParentWBSElementID INT NULL, WBSCode TEXT NOT NULL, Description TEXT NOT NULL, StartDate TEXT NULL,
    EndDate TEXT NULL, EstimatedCost REAL NULL, ActualCost REAL NULL DEFAULT 0.0, Status TEXT NULL,
    CONSTRAINT FK_WBSElements_Projects FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
    CONSTRAINT FK_WBSElements_Parent FOREIGN KEY (ParentWBSElementID) REFERENCES wbs_elements(WBSElementID) ON DELETE CASCADE,
    CONSTRAINT FK_WBSElements_ProcessedEstimates FOREIGN KEY (ProcessedEstimateID) REFERENCES processed_estimates(ProcessedEstimateID) ON DELETE SET NULL,
    CONSTRAINT UK_WBSElements_Project_Code UNIQUE (ProjectID, WBSCode)
);
CREATE INDEX IF NOT EXISTS IX_WBSElements_ProjectID ON wbs_elements (ProjectID);
CREATE INDEX IF NOT EXISTS IX_WBSElements_ParentWBSElementID ON wbs_elements (ParentWBSElementID);

-- Project Budgets
CREATE TABLE IF NOT EXISTS project_budgets (
    BudgetID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INT NOT NULL, WBSElementID INT NULL,
    BudgetType TEXT NOT NULL, Amount REAL NOT NULL, Notes TEXT NULL,
    LastUpdated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_ProjectBudgets_Projects FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
    CONSTRAINT FK_ProjectBudgets_WBSElements FOREIGN KEY (WBSElementID) REFERENCES wbs_elements(WBSElementID) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS IX_ProjectBudgets_ProjectID ON project_budgets (ProjectID);
CREATE INDEX IF NOT EXISTS IX_ProjectBudgets_WBSElementID ON project_budgets (WBSElementID);

-- Actual Costs (Recorded actual project expenditures)
CREATE TABLE IF NOT EXISTS actual_costs (
    ActualCostID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INT NOT NULL, WBSElementID INT NULL, TaskID INT NULL,
    CostCategory TEXT NOT NULL, Description TEXT NOT NULL, Amount REAL NOT NULL, TransactionDate TEXT NOT NULL,
    VendorID INT NULL, PurchaseOrderID INT NULL, Notes TEXT NULL, RecordedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_ActualCosts_Projects FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
    CONSTRAINT FK_ActualCosts_WBSElements FOREIGN KEY (WBSElementID) REFERENCES wbs_elements(WBSElementID) ON DELETE SET NULL,
    CONSTRAINT FK_ActualCosts_Tasks FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID) ON DELETE SET NULL,
    CONSTRAINT FK_ActualCosts_Vendors FOREIGN KEY (VendorID) REFERENCES Vendors(VendorID) ON DELETE SET NULL,
    CONSTRAINT FK_ActualCosts_PurchaseOrders FOREIGN KEY (PurchaseOrderID) REFERENCES PurchaseOrders(PurchaseOrderID) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS IX_ActualCosts_ProjectID ON actual_costs (ProjectID);
CREATE INDEX IF NOT EXISTS IX_ActualCosts_WBSElementID ON actual_costs (WBSElementID);
CREATE INDEX IF NOT EXISTS IX_ActualCosts_TaskID ON actual_costs (TaskID);

-- Progress Updates (Recorded progress of WBS elements or tasks)
CREATE TABLE IF NOT EXISTS progress_updates (
    ProgressUpdateID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INT NOT NULL, WBSElementID INT NULL, TaskID INT NULL,
    UpdateDate TEXT NOT NULL, CompletionPercentage REAL NOT NULL, Notes TEXT NULL, RecordedByEmployeeID INT NULL,
    RecordedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT FK_ProgressUpdates_Projects FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
    CONSTRAINT FK_ProgressUpdates_WBSElements FOREIGN KEY (WBSElementID) REFERENCES wbs_elements(WBSElementID) ON DELETE SET NULL,
    CONSTRAINT FK_ProgressUpdates_Tasks FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID) ON DELETE SET NULL,
    CONSTRAINT FK_ProgressUpdates_Employees FOREIGN KEY (RecordedByEmployeeID) REFERENCES Employees(EmployeeID) ON DELETE SET NULL,
    CONSTRAINT CK_ProgressUpdates_CompletionPercentage CHECK (CompletionPercentage >= 0 AND CompletionPercentage <= 100)
);
CREATE INDEX IF NOT EXISTS IX_ProgressUpdates_ProjectID ON progress_updates (ProjectID);
CREATE INDEX IF NOT EXISTS IX_ProgressUpdates_WBSElementID ON progress_updates (WBSElementID);
CREATE INDEX IF NOT EXISTS IX_ProgressUpdates_TaskID ON progress_updates (TaskID);

-- Material Log Table
CREATE TABLE IF NOT EXISTS MaterialLog (
    MaterialLogID INTEGER PRIMARY KEY AUTOINCREMENT,
    ProjectID INTEGER NOT NULL,
    MaterialStockNumber TEXT NOT NULL, -- Added, for direct reference and consistency
    TaskID INTEGER NULL,               -- Added
    WBSElementID INTEGER NULL,
    QuantityUsed REAL NOT NULL,        -- Renamed from Quantity for clarity
    Unit TEXT NULL,
    CostCode TEXT NULL,
    Supplier TEXT NULL,
    TransactionDate TEXT NOT NULL,     -- Was LogDate, renamed for consistency
    RecordedByEmployeeID INTEGER NULL,
    Notes TEXT NULL,                   -- Added
    MaterialSystemID INTEGER NOT NULL, -- Added
    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
    FOREIGN KEY (MaterialSystemID) REFERENCES Materials(MaterialSystemID) ON DELETE RESTRICT, -- Added FK
    FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID) ON DELETE SET NULL,                         -- Added FK
    FOREIGN KEY (WBSElementID) REFERENCES wbs_elements(WBSElementID) ON DELETE SET NULL,
    FOREIGN KEY (RecordedByEmployeeID) REFERENCES Employees(EmployeeID) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS IX_MaterialLog_ProjectID ON MaterialLog (ProjectID);
CREATE INDEX IF NOT EXISTS IX_MaterialLog_MaterialStockNumber ON MaterialLog (MaterialStockNumber); -- Changed from MaterialName
CREATE INDEX IF NOT EXISTS IX_MaterialLog_TaskID ON MaterialLog (TaskID);                           -- Added
CREATE INDEX IF NOT EXISTS IX_MaterialLog_WBSElementID ON MaterialLog (WBSElementID);
CREATE INDEX IF NOT EXISTS IX_MaterialLog_MaterialSystemID ON MaterialLog (MaterialSystemID);       -- Added

-- Daily Log Tables (for Journeyman Daily Log Integration)
CREATE TABLE IF NOT EXISTS DailyLogs (
    DailyLogID INTEGER PRIMARY KEY AUTOINCREMENT,
    EmployeeID INTEGER NOT NULL,
    ProjectID INTEGER NULL,
    LogDate TEXT NOT NULL,
    JobSite TEXT NULL,
    HoursWorked REAL NULL,
    Notes TEXT NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID) ON DELETE CASCADE,
    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS IX_DailyLogs_EmployeeID ON DailyLogs (EmployeeID);
CREATE INDEX IF NOT EXISTS IX_DailyLogs_ProjectID ON DailyLogs (ProjectID);
CREATE UNIQUE INDEX IF NOT EXISTS UK_DailyLogs_Employee_Date ON DailyLogs (EmployeeID, LogDate);

CREATE TABLE IF NOT EXISTS DailyLogTasks (
    DailyLogTaskID INTEGER PRIMARY KEY AUTOINCREMENT,
    DailyLogID INTEGER NOT NULL,
    TaskDescription TEXT NOT NULL,
    IsCompleted BOOLEAN NOT NULL DEFAULT 0,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (DailyLogID) REFERENCES DailyLogs(DailyLogID) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS IX_DailyLogTasks_DailyLogID ON DailyLogTasks (DailyLogID);

CREATE TABLE IF NOT EXISTS DailyLogMaterials (
    DailyLogMaterialID INTEGER PRIMARY KEY AUTOINCREMENT,
    DailyLogID INTEGER NOT NULL,
    MaterialDescription TEXT NOT NULL,
    Quantity REAL NULL,
    Unit TEXT NULL,
    Type TEXT NULL, -- 'Used' or 'Needed'
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (DailyLogID) REFERENCES DailyLogs(DailyLogID) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS IX_DailyLogMaterials_DailyLogID ON DailyLogMaterials (DailyLogID);

CREATE TABLE IF NOT EXISTS DailyLogObservations (
    DailyLogObservationID INTEGER PRIMARY KEY AUTOINCREMENT,
    DailyLogID INTEGER NOT NULL,
    ObservationType TEXT NOT NULL, -- 'Safety', 'Issue', 'Tool'
    Description TEXT NOT NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (DailyLogID) REFERENCES DailyLogs(DailyLogID) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS IX_DailyLogObservations_DailyLogID ON DailyLogObservations (DailyLogID);


-- New table for detailed WBS Resource/Cost breakdown from estimates
CREATE TABLE IF NOT EXISTS WBSElementResources (
    WBSElementResourceID INTEGER PRIMARY KEY AUTOINCREMENT,
    WBSElementID INTEGER NOT NULL,
    ResourceDescription TEXT NOT NULL, -- e.g., from estimate item description
    ResourceType TEXT,                 -- e.g., 'Material', 'Labor', 'Equipment', 'Subcontractor'
    Quantity REAL,
    UnitOfMeasure TEXT,
    UnitCost REAL,
    TotalEstimatedCost REAL,
    Notes TEXT,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (WBSElementID) REFERENCES wbs_elements(WBSElementID) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS IX_WBSElementResources_WBSElementID ON WBSElementResources (WBSElementID);

-- End of Application Core Tables --

-- == New Tables for LLM Parsing, Purchasing Log, and Production Tracking ==

-- LLM_Parsed_Data_Log Table
CREATE TABLE LLM_Parsed_Data_Log (
    ParsedDataID INTEGER PRIMARY KEY AUTOINCREMENT,
    SourceModule TEXT NOT NULL, -- e.g., 'DailyLog', 'MaterialRequest', 'SiteObservation'
    SourceRecordID INTEGER NULL, -- ID of the record in the original table, if applicable
    OriginalInput TEXT NOT NULL, -- The raw text input the LLM processed
    ParsedJSON TEXT NOT NULL, -- JSON string of the structured data extracted by the LLM
    ConfidenceScore REAL NULL, -- LLM's confidence in parsing, if available
    ParsingTimestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ReviewStatus TEXT NOT NULL DEFAULT 'Pending Review', -- e.g., 'Pending Review', 'Approved', 'Rejected', 'Corrected'
    ReviewedByEmployeeID INTEGER NULL,
    ReviewDate TEXT NULL,
    Notes TEXT NULL,
    FOREIGN KEY (ReviewedByEmployeeID) REFERENCES Employees(EmployeeID) ON DELETE SET NULL,
    -- Potential FK to other tables based on SourceModule and SourceRecordID would require dynamic handling or separate linking tables.
    -- For now, SourceRecordID is informational.
    CHECK (ReviewStatus IN ('Pending Review', 'Approved', 'Rejected', 'Corrected'))
);
CREATE INDEX IX_LLM_Parsed_Data_Log_SourceModule_RecordID ON LLM_Parsed_Data_Log (SourceModule, SourceRecordID);
CREATE INDEX IX_LLM_Parsed_Data_Log_ReviewStatus ON LLM_Parsed_Data_Log (ReviewStatus);
CREATE INDEX IX_LLM_Parsed_Data_Log_ParsingTimestamp ON LLM_Parsed_Data_Log (ParsingTimestamp);

-- Purchasing_Log Table
CREATE TABLE Purchasing_Log (
    InternalLogID INTEGER PRIMARY KEY AUTOINCREMENT,
    ProjectID INTEGER NULL,
    RequestedByEmployeeID INTEGER NOT NULL,
    MaterialDescription TEXT NOT NULL,
    QuantityRequested REAL NOT NULL,
    UnitOfMeasure TEXT NULL,
    UrgencyLevel TEXT NULL, -- e.g., 'Standard', 'Urgent', 'Critical'
    RequiredByDate TEXT NULL, -- YYYY-MM-DD
    Status TEXT NOT NULL DEFAULT 'Requested', -- e.g., 'Requested', 'Approved by PM', 'PO Issued', 'Received Partial', 'Received Full', 'Cancelled'
    AssociatedPOLineItemID INTEGER NULL,
    Notes TEXT NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE SET NULL,
    FOREIGN KEY (RequestedByEmployeeID) REFERENCES Employees(EmployeeID) ON DELETE RESTRICT,
    FOREIGN KEY (AssociatedPOLineItemID) REFERENCES PurchaseOrderLineItems(POLineItemID) ON DELETE SET NULL,
    CHECK (UrgencyLevel IN ('Standard', 'Urgent', 'Critical') OR UrgencyLevel IS NULL),
    CHECK (Status IN ('Requested', 'Approved by PM', 'PO Issued', 'Received Partial', 'Received Full', 'Cancelled'))
);
CREATE INDEX IX_Purchasing_Log_ProjectID ON Purchasing_Log (ProjectID);
CREATE INDEX IX_Purchasing_Log_RequestedByEmployeeID ON Purchasing_Log (RequestedByEmployeeID);
CREATE INDEX IX_Purchasing_Log_Status ON Purchasing_Log (Status);
CREATE INDEX IX_Purchasing_Log_RequiredByDate ON Purchasing_Log (RequiredByDate);

-- Production_Assembly_Tracking Table
CREATE TABLE Production_Assembly_Tracking (
    ProductionID INTEGER PRIMARY KEY AUTOINCREMENT,
    AssemblyID INTEGER NOT NULL,
    ProjectID INTEGER NULL,
    QuantityToProduce REAL NOT NULL,
    Status TEXT NOT NULL DEFAULT 'Planned', -- e.g., 'Planned', 'In Progress', 'On Hold', 'Completed', 'QC Passed', 'Shipped'
    StartDate TEXT NULL, -- YYYY-MM-DD
    CompletionDate TEXT NULL, -- YYYY-MM-DD
    AssignedToEmployeeID INTEGER NULL, -- Foreman/Lead of production
    Notes TEXT NULL,
    DateCreated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (AssemblyID) REFERENCES Assemblies(AssemblyID) ON DELETE RESTRICT,
    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE SET NULL,
    FOREIGN KEY (AssignedToEmployeeID) REFERENCES Employees(EmployeeID) ON DELETE SET NULL,
    CHECK (Status IN ('Planned', 'In Progress', 'On Hold', 'Completed', 'QC Passed', 'Shipped'))
);
CREATE INDEX IX_Production_Assembly_Tracking_AssemblyID ON Production_Assembly_Tracking (AssemblyID);
CREATE INDEX IX_Production_Assembly_Tracking_ProjectID ON Production_Assembly_Tracking (ProjectID);
CREATE INDEX IX_Production_Assembly_Tracking_Status ON Production_Assembly_Tracking (Status);
CREATE INDEX IX_Production_Assembly_Tracking_AssignedToEmployeeID ON Production_Assembly_Tracking (AssignedToEmployeeID);

-- Database Schema Creation Script Completed Successfully!

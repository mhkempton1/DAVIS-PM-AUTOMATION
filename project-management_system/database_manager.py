import sqlite3

class DatabaseManager:
    def __init__(self, db_name="pm_system.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def disconnect(self):
        if self.conn:
            self.conn.close()

    def _create_tables(self):
        # Productivity_WBS table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Productivity_WBS (
            WBS_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ProjectID INTEGER,
            Parent_ID INTEGER,
            Name TEXT NOT NULL,
            Description TEXT,
            BudgetedHours REAL,
            WorkType TEXT CHECK(WorkType IN ('Field', 'Prefab'))
        );
        """)

        # Productivity_DailyLog table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Productivity_DailyLog (
            Log_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            WBS_ID INTEGER,
            LogDate TEXT NOT NULL,
            CrewSize INTEGER,
            HoursWorked REAL,
            QuantityInstalled REAL,
            PercentComplete REAL,
            ReasonCodeID INTEGER,
            FOREIGN KEY (WBS_ID) REFERENCES Productivity_WBS(WBS_ID),
            FOREIGN KEY (ReasonCodeID) REFERENCES Productivity_ReasonCodes(ReasonCodeID)
        );
        """)

        # Productivity_ReasonCodes table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Productivity_ReasonCodes (
            ReasonCodeID INTEGER PRIMARY KEY AUTOINCREMENT,
            Code TEXT NOT NULL UNIQUE,
            Description TEXT
        );
        """)
        # TODO: Add other tables from the existing system if any

        self.conn.commit()

    # TODO: Add methods for CRUD operations for each table

if __name__ == '__main__':
    # Example usage:
    db_manager = DatabaseManager()
    db_manager.connect()
    # You can add some initial data or test queries here
    # Example: Pre-populate reason codes
    try:
        db_manager.cursor.execute("INSERT INTO Productivity_ReasonCodes (Code, Description) VALUES ('MAT', 'Material Availability')")
        db_manager.cursor.execute("INSERT INTO Productivity_ReasonCodes (Code, Description) VALUES ('EQU', 'Equipment Issue')")
        db_manager.cursor.execute("INSERT INTO Productivity_ReasonCodes (Code, Description) VALUES ('LAB', 'Labor Shortage')")
        db_manager.cursor.execute("INSERT INTO Productivity_ReasonCodes (Code, Description) VALUES ('WEA', 'Weather Delay')")
        db_manager.cursor.execute("INSERT INTO Productivity_ReasonCodes (Code, Description) VALUES ('RFI', 'Request for Information')")
        db_manager.cursor.execute("INSERT INTO Productivity_ReasonCodes (Code, Description) VALUES ('CLN', 'Client/Owner Delay')")
        db_manager.cursor.execute("INSERT INTO Productivity_ReasonCodes (Code, Description) VALUES ('DES', 'Design/Coordination Issue')")
        db_manager.cursor.execute("INSERT INTO Productivity_ReasonCodes (Code, Description) VALUES ('SAF', 'Safety Stoppage')")
        db_manager.cursor.execute("INSERT INTO Productivity_ReasonCodes (Code, Description) VALUES ('OTH', 'Other')")
        db_manager.conn.commit()
    except sqlite3.IntegrityError:
        # Codes already exist, which is fine for this example run.
        pass

    print("Database and tables created/verified. Pre-populated reason codes.")
    db_manager.disconnect()

## Legend
### + Features/Added
### - Bugs/Fixed/Removed
### Date dd-mm-yyyy

## Version 8.4.1 -> 8.4.2 (27-04-2026)
### Added
    + Pagination in data import controller
    + Page size field in table to set page size


## Version 8.4.0 -> 8.4.1 (05-12-2025)
### Fixed
    - Error during workspace user add in SP method


## Version 8.3.0 -> 8.4.0 (26-09-2025)
### Added
    + Import type Datasets support
    + Web token and user API key authentication for import type dataset
    + Option to regenerate the web token
    + Option to create record from dashboard item
    + requirements.txt file for python dependency
### Updated
    + Connector dashboard item can not be open
    + App credentials changed to password type
    + Error handling in dashboard item graph data
    + Connector Dashboard UI enhancement (coloured graph and menu)
    + Error messages/logs in chatter
    + Hide search bar and pager in connector dashboard
    + Other stability updates
### Fixed
    - Report embed issue if its connected dataset is not available on odoo in default workspace


## Version 8.2.5 -> 8.3.0 (03-07-2025)
### Added
    + Record sync limit
    + Option to add users in newly created workspace in SP method
    + Option to unpublish a kql database
    + Data export mode (All/Incremental)
    + Option to unpublish a table in kql database
### Updated
    + Checking parent item status before publish/unpublish any item
    + Updating last sync date from last record instead of current date
    + Made column labels unique per table
    + Other stability and view level updates
### Fixed
    - Create date field issue in reporting models, now checking date field in model
    - Rec name issue, now checking if rec name is available else using other name fields


## Version 8.2.4 -> 8.2.5 (09-05-2025)
### Fixed
    - Table & Column creation issue due to constrain
### Updated
    + Some view level updates


## Version 8.2.3 -> 8.2.4 (07-05-2025)
### Added
    + Timezone selection to sync datetime in specific timezone
    + Table and Column name validation
    + ID column by default in database table
### Fixed
    - Selection of one2many field
    - Creation of double Id column in dataset table
    - Other view and stability updates


## Version 8.2.2 -> 8.2.3 (05-05-2025)
### Fixed
    - Datasets menu hide issue


## Version 8.2.1 -> 8.2.2 (02-04-2025)
### Fixed
    - Data type issue during table publish


## Version 8.2.0 -> 8.2.1 (27-03-2025)
### Fixed
    - Ingestion/Query service URI in SP method


## Version 8.1.0 -> 8.2.0 (27-02-2025)
### Added
    + Datasets (removed in last release)
    + Configuration to switch between PowerBI and Fabric items


## Version 8.0.0 -> 8.1.0 (20-01-2025)
    Module is now compatible with PowerBI's RTI (Real-Time Intelligence) feature
### Added
    + Eventhouse in workspaces
    + KQL Database in Eventhouse
    + Other stability updates according to new features
### Removed
    - Dataset from workspace
    - Wizard for adding table column


## Version 7.1.2 -> 8.0.0 (14-08-2024)
    Module is now compatible with Odoo v18


## Version 7.1.1 -> 7.1.2 (14-08-2024)
### Added
    + Option to select all columns automatically in table
    + Validating no of columns to 75 during dataset publish
### Updated
    + Changed responsible user from single to multiple in workspace
    + Other stability updates


## Version 7.1.0 -> 7.1.1 (15-07-2024)
### Added
    + Support of many2many field in table
    + Tracking of filter domain in table
### Fixed
    - Table creation issue
    - Overrided table column's create method in batch (model_create_multi)
### Removed
    - Selection of transient model in dataset


## Version 7.0.0 -> 7.1.0 (17-04-2024)
### Added
    + Table relationship based on many2one field
    + Controller for redirect URI
    + Auto redirect in case of api consent error during test connection
    + Custom field/column labels
    + Filters and groups in workspace, datasets and tables
    + Validation in table to check relationship
### Removed
    - Parent-Child relation between table columns
    - Deprecated service principal connection method
### Fixed
    - Installation warnings


## Version 6.2.1 -> 7.0.0 (10-11-2023)
### Added
    Module is now compatible with Odoo v17
    + Computing default workspace or dataset when creating new dataset or table respectively
### Fixed
    - Data export issue in tables (memory limit exceed)


## Version 6.2.0 -> 6.2.1 (20-07-2023)
### Added
    + Table count in datasets
    + Report and dashboard count in workspaces
### Fixed
    - Using odoo field description as powerbi column name instead of adding parent and child fields


## Version 6.1.0 -> 6.2.0 (30-06-2023)
### Added
    + Last sync date to avoid duplicity on PowerBI end
    + Warning message for schema update
    + Other message level updates
### Removed
    - powerbi.snipper model
    - Report and Dashboard wizards


## Version 6.0.1 -> 6.1.0 (16-05-2023)
### Added
    + Option to unpublish a dataset from odoo
    + Reset connection
    + Chatter for logging error/success messages and conversations
    + Odoo dashboard for overall summary of published and unpublished records
    + Confirmation messages during data export/delete and schema update
    + Responsible user and object counts in workspace
    + Record rules to streamline access management
    + Connection states management
    + Option to configure cron from connection
    + Other view level and stability updates
### Fixed
    - Report and dashboard render issue
### Removed
    - Sync history model
    - Publish server actions from workspace and datasets


## Version 6.0.0 -> 6.0.1 (25-01-2023)
### Added
    + Support for PowerBI's "My Workspace" (Default workspace)
### Fixed
    - Data type issue in date/datetime fields


## Version 3.2.0 -> 6.0.0 (18-11-2022)
### Added
    Module is now compatible with Odoo v16
    + Minor view level updates
### Removed
    - Required field check on connection create method, made required in form view


## Version 3.1.1 -> 3.2.0 (22-03-2022)
## Fixed
    - Rows limit issue in API, using batch of 10k rows


## Version 2.0.1 -> 3.1.1 (17-03-2022)
### Added
    + Openid scope during connection
    + Minor stability updates


## Version 2.0.0 -> 2.0.1 (11-02-2022)
### Added
    + All the required api scopes during connection


## Version 1.0.0 -> 2.0.0 (04-10-2021)
### Added
    Module is now compatible with Odoo v15
    + Cron to export data
    + Wizard to update connection credentials
    + Api consent permission error with complete url to hit on browser for api permissions
    + Creation/Deletion of server actions from tables
    + Web Ribbon widget for connection status
    + Other view level and stability updates


## Version 1.0.0 (20-07-2021) (Initial Release)
### Features
    + Import/Export workspaces
    + Export datasets with tables
    + Export/Delete data in tables for any odoo model
    + Update the table schema on PowerBI from Odoo
    + Import PowerBI reports and dashboards on Odoo
    + Embedd PowerBI reports and dashboard on Odoo

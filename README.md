# Cloud Scanner & Cost Estimator

## Prerequisites

* **Python 3.9+**
* **Boto3** (`pip install boto3`)
* **AWS Credentials** configured in the environment.

## Permissions

The script relies on the default cross-account role mechanism.

* **Management Account (Runner):**
    * `organizations:ListAccounts`
    * `organizations:DescribeOrganization`
    * `sts:AssumeRole`
* **Member Accounts (Target):**
    * Role: `OrganizationAccountAccessRole` (must exist)
    * Policy: `ReadOnlyAccess` (or equivalent permissions for EC2, Lambda, S3, AutoScaling)

## Installation

```bash
git clone https://github.com/BenjaminVolodarsky/scanner-cost-estimator-dev.git
cd scanner-cost-estimator-dev
```
* If boto3 is not already installed (e.g. outside CloudShell):
```bash
pip install boto3
```

# Usage
Run the script:
```bash
./upwind
```
* To specify a custom cross-account role name:

```bash
./upwind --role CustomRoleName
```
* Management Account should Scan all active member accounts in the Organization, if given the right permissions and policies as outlined in the Permissions section.

* Member Account: Scans only the *local account*.

### Output
Results are generated in the output/ directory:

* output.csv: Flat resource list (Account, Region, Type, Specs).
----
## Troubleshooting
### Partial scan / Missing permissions:
* If logs indicate missing permissions for a specific account, ensure the OrganizationAccountAccessRole in that member account has the ReadOnlyAccess policy attached.

* OrganizationAccountAccessRole missing:
If the role cannot be assumed, it may not exist (common in invited accounts). Create the role manually in the member account and trust the Management Account ID.
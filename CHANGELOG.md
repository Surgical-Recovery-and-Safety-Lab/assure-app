# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to Semantic Versioning ([SemVer](https://semver.org/spec/v2.0.0.html)).

## [1.5.0] - 2026-10-24

### Added
* Security features for the feedback button with timeout and rate limits to 
limit spamming.
* A timeout constant that stops the process if the email was not sent in time.
* Safety feature to avoid showing tracebacks to users if there is an error.
* A `UNAVAILABLE_KEYS` constant so that regressor outcomes work properly.
* Validation of the feedback form: valid email address, maximum lengths for the
email, subject and message, and no line breaks in the email or subject to
prevent email header injection.
* An error message in the feedback form if the message could not be sent.
* A `scripts/sync_assets.sh` script that copies only the assets used by the app
from the test deployment to production, and fails if any of them is missing.
* A `constraints.txt` file with the exact versions of all dependencies, used
when installing them on the servers.
* A `CI` workflow that compiles the code and runs the new tests on pull
requests and pushes to `main` and `app-dev`.
* Tests for the input conversion, the feedback validation and the risk status.
* Dependabot configuration to keep the pinned GitHub actions up to date.
* The date in the PDF report is now in the timezone of the user's browser.

### Changed
* In case of a tie with population average, the text now read `Equal` rather
than `Lower`. The text is black in the charts, tables and PDF report.
* The risk status is now compared at the displayed precision, so values that
look the same are no longer shown as `Higher`.
* The feedback form no longer hangs or shows the error details, which could
include the feedback URL, if the message cannot be sent.
* The deployment workflows use a pinned version of the SSH action, stop at the
first failing command, have read-only permissions and do not run concurrently.
* The production deployment no longer copies the whole assets folder from the
test deployment.
* `requirements.txt` now lists the packages imported directly by the app
(`numpy`, `pandas` and `requests`) and no longer lists the unused `fpdf2`.
* Removed the unused `LEGEND_LOWER` and `LEGEND_HIGHER` constants and the unused
variables on the main page.
* The PDF report uses the bundled DejaVu Sans font rather than `Segoe UI`, which
is not available on the servers.
* The text in the PDF report is now HTML escaped.
* The dev container folder was renamed from `.devcontainer ` (with a trailing
space) to `.devcontainer` and now uses Python 3.12, `app.py` and the
`constraints.txt` file.
* The consent text now says that the information is only kept temporarily in the
memory of the server during the session, rather than that it is deleted when the
window is closed.
* Added a docstring to `reporting.py`.
* The code now passes `ruff check`, `ruff format` and `mypy`. The tool versions are
in `requirements-dev.txt`, the `mypy` settings in `pyproject.toml`, and the CI
workflow runs all three.

### Fixed
* Bugs with the `Run model` button that did not work after changing pages.
* The `Run model` button was always enabled, it is now disabled until all the
fields are filled in.
* The results are now kept consistent with the inputs used to run the model,
and a warning is displayed if the inputs change after running it.
* Results from the previous patient no longer remain after leaving the
calculator page.
* Bug with `Prior cancer` and `Trauma` that were always True.
* Missing key `KeyError` would be raised if category L2 was missing.
* Display issue where the `Help` popover for ASA and operations was below 
rather than on the right.
* The PDF is only generated after clicking the download button rather than 
every time a figure is regenerated.
* The `MIME` for the PDF download button is now a pdf rather than an
octet-stream.
* Rounding the confidence intervals for the regressor values rather than using
ceiling.
* Display issues of information messages if classifier charts were not
displayed.
* Typos on the about page ("Surgical") and in the ASA help (American Society of
Anesthesiologists), the transfer help text, the operation search help and in
code comments.
* The about page said "No data is **not** collected", it now says that the data
is **not** collected, as on the home page.
* Master toggle syncing now works both ways and users don't need to toggle 
three times to sync if there was an issue. 

## [1.4.0] - 2026-10-23

### Changed
* Bumped medpipe version from 0.3.1 to 0.4.0.dev2
* Loading function now uses the new `MedpipeClassifier` or `MepipeRegressor`
loading functions
* Split the `data_visualisation` function into smaller functions placed in the new
`visualisation.py` file
* The PDF report shows 'No outcomes selected' is the user does not tick any outcomes
* Reviewed the data visualisation to have the patient as a point and the 
population average as a rectangle.
* The `Help` button for explaining the charts has been updated to `How to read
the charts` and includes information about the regression outcomes.
* Updated the model version from v1 to v2 for classifiers and regressors.

### Added
* New data conversion function to make the format fit with the new medpipe version
* The `MedpipeRegressor` inference
* The `reoperation` complication to the list of complications
* A legend for the graph representations
* Encoded y values for graphical display to avoid truncating the complications
* A `src/` folder that contains the helper functions
* Visualisation for the regressor results DAOH and LOS as table and graph
* Exporting regressor results to the PDF report
* Created a `reporting.py` script for PDF report generation
* Proper docstring and type hinting
* New regression outcomes for days alive and out of hospital and length of 
stay.

### Removed
* Removed old data type conversion function

### Fixed
* Typo in the ethnicity input for Pacific Peoples.
* Case when the CI are None.

## [1.3.1] - 2026-07-28

### Changed
* Updated the workflow to test the app on the Nectar server
* Updated the workflow to deploy the app on the Nectar server
* Changed layout of the mortality buttons from horizontal to vertical
* Fixed visual bug between chart and graph

## [1.3.0] - 2026-07-27

### Added
* Added CHANGELOG.md

### Changed
* Using medpipe v0.3.1 now
* Minor tweaks to adapt to API changes in medpipe
* Changed model created using medpipe v0.3.1

## [1.2.4] - 2026-06-11

### Changed
* Made the tabs bold font
* Updated model version

## [1.2.3] - 2026-05-26

### Added
* Search bar to identify category level 1 and 2, and operation severity

### Changed
* New logos
* Minor change to README.md

## [1.2.1] - 2026-05-11

### Added
* Created a health service use tab with readmission outcomes
* Added FTR, DAOH, and LOS as coming soon
* Added automated deployment on main and deploy branches

### Changed
* Minor verbiage change in the webapp text
* Updated model version

## [1.2.0] - 2026-04-29

### Changed
* Minor issues fixed
* Updated model version
* Renamed from ASSuRE to ASSURE
* Improved graphical visualisation of results
* Changed medpipe version

## [1.1.0] - 2026-04-23

### Added
* Added pages and navigation side bar
* Feedback from using Formspree

### Changed
* Updated graph views
* Small adjustments to make navigation easier

## [1.0.1] - 2026-04-15

### Changed
* Minor bug fixes
* UI changes to fit new number of complications

## [1.0.0] - 2026-04-15

### Changed
* New interface
* Reduced number of input parameters
* Improved visulisation of results

## [0.0.1] - 2026-02-23

### Added
* First version


[Unreleased]: https://github.com/Surgical-Recovery-and-Safety-Lab/assure-app/compare/v1.5.0...HEAD
[1.5.0]: https://github.com/Surgical-Recovery-and-Safety-Lab/assure-app/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/Surgical-Recovery-and-Safety-Lab/assure-app/compare/v1.3.1...1.4.0
[1.3.1]: https://github.com/Surgical-Recovery-and-Safety-Lab/assure-app/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/Surgical-Recovery-and-Safety-Lab/assure-app/compare/v1.2.4...v1.3.0
[1.2.4]: https://github.com/Surgical-Recovery-and-Safety-Lab/assure-app/compare/v1.2.3...v1.2.4
[1.2.3]: https://github.com/Surgical-Recovery-and-Safety-Lab/assure-app/compare/v1.2.1...v1.2.3
[1.2.1]: https://github.com/Surgical-Recovery-and-Safety-Lab/assure-app/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/Surgical-Recovery-and-Safety-Lab/assure-app/compare/v.1.1.0...v1.2.0
[1.1.0]: https://github.com/Surgical-Recovery-and-Safety-Lab/assure-app/compare/v1.0.1...v.1.1.0
[1.0.1]: https://github.com/Surgical-Recovery-and-Safety-Lab/assure-app/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/Surgical-Recovery-and-Safety-Lab/assure-app/compare/v0.0.1...v1.0.0
[0.0.1]: https://github.com/Surgical-Recovery-and-Safety-Lab/assure-app/releases/tag/v0.0.1

# [1.11.0](https://github.com/rad-solutions/webserver/compare/v1.10.0...v1.11.0) (2025-06-25)


### Features

* add semantic release workflow test ([a367a2b](https://github.com/rad-solutions/webserver/commit/a367a2b38f64e98bfeb40f51353bbac961c89072))
* add semantic release workflow test ([2614103](https://github.com/rad-solutions/webserver/commit/2614103b6fd9f64e4ad531f67d24105c93d35db1))
* add semantic release workflow test ([6a981c2](https://github.com/rad-solutions/webserver/commit/6a981c2e73a039e95356412190cb65f565e61e90))
* add semantic release workflow test ([d2e3103](https://github.com/rad-solutions/webserver/commit/d2e3103258ce56b403bd1c7df30d0de521b04a5b))
* add semantic release workflow test 4 ([6aef11c](https://github.com/rad-solutions/webserver/commit/6aef11cb5349db034f46abcdd9ecc8470d4d04d0))
* add semantic release workflow test 5 ([9a75d98](https://github.com/rad-solutions/webserver/commit/9a75d988d96ee81bf704335116de0758612e5dc1))
* add semantic release workflow test 6 ([50b8f1a](https://github.com/rad-solutions/webserver/commit/50b8f1a3a5450e646bc6de6f2a5e70bad0363904))

# [1.10.0](https://github.com/rad-solutions/webserver/compare/v1.9.0...v1.10.0) (2025-06-25)


### Features

* Implement dynamic report titles for equipment ([de256aa](https://github.com/rad-solutions/webserver/commit/de256aa54550fd261a3c8140034270e27f9b6bc7))

# [1.9.0](https://github.com/rad-solutions/webserver/compare/v1.8.0...v1.9.0) (2025-06-25)


### Features

* Added UI for Process Assignment and control of time spent by internal users. Corresponding tests added. ([1e30e24](https://github.com/rad-solutions/webserver/commit/1e30e24ad45a7441f9db42853d84b3b3b6db46c4))

# [1.8.0](https://github.com/rad-solutions/webserver/compare/v1.7.0...v1.8.0) (2025-06-24)


### Features

* Add x-ray fields and changes history ([0b5b400](https://github.com/rad-solutions/webserver/commit/0b5b400854cdea7d5f3308afc085a046fe56f0fb))

# [1.7.0](https://github.com/rad-solutions/webserver/compare/v1.6.0...v1.7.0) (2025-06-24)


### Features

* Add process assignment and time tracking ([2005a75](https://github.com/rad-solutions/webserver/commit/2005a755b68f55a3c49efc77752f4dd833abb41b))

# [1.6.0](https://github.com/rad-solutions/webserver/compare/v1.5.0...v1.6.0) (2025-06-20)


### Features

* Added user permissions and edition view implemented. Corresponding test added. ([9d06b36](https://github.com/rad-solutions/webserver/commit/9d06b362b5341007d96ee7966e10ad6c029ff16e))
* User creation dynamically showing fields for Client Profile if they apply. Corresponding test added. ([9edb9f1](https://github.com/rad-solutions/webserver/commit/9edb9f1ffc9d588c95b19613b3d3d053db757f62))

# [1.5.0](https://github.com/rad-solutions/webserver/compare/v1.4.0...v1.5.0) (2025-06-19)


### Features

* Added new form to update the progress of a process and/or the status of the process. Added corresponding test in test_process.py ([c408a70](https://github.com/rad-solutions/webserver/commit/c408a70fcdcf77f448b3843b5cea7a92792357ee))
* Added progress bar to client's dashboard and process_detail. ([c4a2598](https://github.com/rad-solutions/webserver/commit/c4a25986c39cc7338aead56246c9b20f5db07e6c))
* When creating an "Asesoria" process, the user is now asked to complete the ProcessCategory field. This field is hidden by default and for other process types. This ensures proper checklist_items creation. ([a21bb6c](https://github.com/rad-solutions/webserver/commit/a21bb6c5b021e245e32d031ca6b2373e0ab2cc7e))

# [1.4.0](https://github.com/rad-solutions/webserver/compare/v1.3.0...v1.4.0) (2025-06-17)


### Features

* Added Anotacion view in process_detail and anotacion_create view. Implemented permissions to anotacion_create. ([3d29618](https://github.com/rad-solutions/webserver/commit/3d2961802f98b3a80e2e5c3dcb089f420dcac2ca))
* Added Asesorias items for follow up ([ef36650](https://github.com/rad-solutions/webserver/commit/ef366508bdbdc4eca2164c23d2378d2d50528ab0))
* Added filters by date on equipos_list and process_list pages. Added corresponding tests for the new filters. ([49627d0](https://github.com/rad-solutions/webserver/commit/49627d00bc366a2a9bd3dd05676ff06e3ac7b4b6))
* Added message in process_list and fixed colours of the sidebar. ([19f7e46](https://github.com/rad-solutions/webserver/commit/19f7e4644ebb20c74ba45c3a9d5d15a04ba8c5c9))
* Added notification section for quality control expiration. Respective tests added. Re-organization of the test_views.py into smaller python files by component. ([34bfe26](https://github.com/rad-solutions/webserver/commit/34bfe26c95d11c4180f9bbe20065044504caa502))
* Added pdf extension validation and corresponding test. ([517120a](https://github.com/rad-solutions/webserver/commit/517120af3c5ad44c62c5e35d5838f7bb56adfeb7))
* added populate-db make command ([5cff862](https://github.com/rad-solutions/webserver/commit/5cff8621364f7e97001cfcb95b61420958b74422))
* agregar nuevos permisos requeridos y tests asociados ([717be14](https://github.com/rad-solutions/webserver/commit/717be1449d14dfd65ca756990c42b483d8c3c3d1))
* Anotacion Model and Tests ([ddc5ceb](https://github.com/rad-solutions/webserver/commit/ddc5ceb8668d7c7f861dfef0c3df426062a88b8e))
* Changes to client's dashboard. Fixed discrepancies in the equipos_detail page. Fixed responsiveness. Updated tests to match the current status of the webserver. ([cc5019d](https://github.com/rad-solutions/webserver/commit/cc5019ddfdf313cd0e1e70510fe8b916e1e721a7))
* Client's main dashboard ([b68642c](https://github.com/rad-solutions/webserver/commit/b68642c4bd6245f95cfcc539e7a8108978dba0ec))
* Dashboard now loads equipment by asociated processes via reports or directly using the asociated process of the equipment. ([3693d2e](https://github.com/rad-solutions/webserver/commit/3693d2e3e52f8399a2c7699636f43fc60c8d200b))
* Dashboard Redesign, added filters to Report List and updated test to match the new Dashboard logic and reports filters. ([1c1e877](https://github.com/rad-solutions/webserver/commit/1c1e8778cf1cabe1b66df21cf5c84bc9990c2439))
* Equipos now showing last cc report and history of cc reports using model's methods. Updated respective tests. ([45b3568](https://github.com/rad-solutions/webserver/commit/45b35689b4229763129c4e9bf40ba6fff971f72a))
* Fixed buttons "Volver" and "Cancelar" so that it takes the user to the previous visited page correctly. ([a3175cb](https://github.com/rad-solutions/webserver/commit/a3175cb41c29b267469dfe5ec4fafd5ff235cc90))
* Fixed permissions error on a test. ([b129814](https://github.com/rad-solutions/webserver/commit/b129814c92055062eeee8276b66355256920a76f))
* Handler functions for equipment class ([aa493f8](https://github.com/rad-solutions/webserver/commit/aa493f89d46c84f10a4a2f0b4b3a37784c433762))
* Implement custom roles and permissions system ([c14760d](https://github.com/rad-solutions/webserver/commit/c14760d50f64264810211ed075cbca1589082714))
* Implemented dynamic buttons in equipos_detail page depending on the active processes associated to the equipment (via reports and directly). No need to update tests. ([1a9f360](https://github.com/rad-solutions/webserver/commit/1a9f360b668b24e93eab2371497d2dad6e0866c8))
* Improved forms to create and update Reports and Equipment filtering processes and equipment (if applicable) by selected user updating dynamically. ([a1d25d0](https://github.com/rad-solutions/webserver/commit/a1d25d0c04ae56208fed64827091ecd4d0692097))
* Improved the visualization of the filters in the _list pages. Added process_status filter on process_list, now showing equipment filter on reports_list and fixed cc+equipment filter redirected from equipos_detail to reports_list. ([ad1590d](https://github.com/rad-solutions/webserver/commit/ad1590d3a8f6d645f1811cbc82ca08ffb7b78766))
* Improved visualization of filters in equipos_list. ([06bb068](https://github.com/rad-solutions/webserver/commit/06bb0687e01883eca5bd4f88f5931227a3040137))
* New filter by model or serial number in equipos_list page. Corresponding tests added. ([d8e4ee7](https://github.com/rad-solutions/webserver/commit/d8e4ee7573334afed4137d90c4af46de702b5639))
* New navbar colours. Fixed visibility of buttons in reports list depending on permissions. ([03be798](https://github.com/rad-solutions/webserver/commit/03be798d5f7fcbaa26288d6feccc159a96b1f03d))
* Permissions implemented in views, and templates. Corresponding tests updated. ([678f966](https://github.com/rad-solutions/webserver/commit/678f966ae2b12698bc8799cccad9b2fc2e3fe908))
* Process model checklist handlers ([602f0ca](https://github.com/rad-solutions/webserver/commit/602f0ca5374f25567d4cf51d471d19db5e21d1e5))
* Responsive check ([c4ef6f8](https://github.com/rad-solutions/webserver/commit/c4ef6f8c8a7dd411ea98a5e080c2916ac570c379))
* Simplified the anotacion_create view and implemented tests for the anotacion view. ([165a9cf](https://github.com/rad-solutions/webserver/commit/165a9cf3e7ca045f36b46129e5944ba71e64b2f2))
* Testing client's dashboard ([dabf666](https://github.com/rad-solutions/webserver/commit/dabf666d33514307fe96251e4cae1b8eda5dbacf))
* Tests for new filters (Process Status in process_list) and fixed inconsistencies. ([ee59bba](https://github.com/rad-solutions/webserver/commit/ee59bba7fe57822a523439c3140f25a3ab10bf01))
* Tests for process, equipment and reports UI. Refactor to match with updated models ([69ca356](https://github.com/rad-solutions/webserver/commit/69ca356238edaec0cebe133759b3883cf0101954))
* UI for creation, update, delete, and view procesos, equipos and update pages for reports. Also, minor fixes in the dashboard. ([daba60d](https://github.com/rad-solutions/webserver/commit/daba60d5be99be78944885f72a56e0f187ab6d91))
* Updated dates on test to mantain correctness in the future. ([304a1c0](https://github.com/rad-solutions/webserver/commit/304a1c038d975e4eb0d18e575b01c042ae790e5f))

# [1.3.0](https://github.com/rad-solutions/webserver/compare/v1.2.0...v1.3.0) (2025-05-15)


### Features

* Integrate Poetry ([7988053](https://github.com/rad-solutions/webserver/commit/7988053e01182a7e631f1cf42346964bfa2b7628))

# [1.2.0](https://github.com/rad-solutions/webserver/compare/v1.1.0...v1.2.0) (2025-05-12)


### Features

* Added semantic release and new fields to the database ([53ceaf2](https://github.com/rad-solutions/webserver/commit/53ceaf22fcf8dfd7fd7f043cd4fdcfdc3c04c3fa))

# [1.1.0](https://github.com/rad-solutions/webserver/compare/v1.0.0...v1.1.0) (2025-05-08)


### Features

* Added error test ([577dd50](https://github.com/rad-solutions/webserver/commit/577dd507fe96eee17b6c0d83c6462df73f931f19))

# 1.0.0 (2025-05-08)


### Features

* Add Role model with choices and link to User ([bbcd1e7](https://github.com/rad-solutions/webserver/commit/bbcd1e7779744c023bb0a9cef39700f50f2ac677))
* Define Process, Equipment, and related models ([594fd12](https://github.com/rad-solutions/webserver/commit/594fd120f747d2cb9b353aa4045bd7f8c348d071))
* Define Process, Equipment, Report models and apply formatting ([6341b21](https://github.com/rad-solutions/webserver/commit/6341b21d31bc771b985de4826b2125eecb3f8570))
* Implement user roles, processes, and equipment ([24c639a](https://github.com/rad-solutions/webserver/commit/24c639a1c66029e59bb06aeee7e1f132d950b6f2))
* Testing semantic release ([79ee38b](https://github.com/rad-solutions/webserver/commit/79ee38b2658bc8f8f0c587c209b565f0ad819c05))
* Testing semantic release 2 ([62b1f80](https://github.com/rad-solutions/webserver/commit/62b1f80c5cf5317fb669ee6fd97a2a02bead34e1))

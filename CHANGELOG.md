# [1.53.0](https://github.com/rad-solutions/webserver/compare/v1.52.0...v1.53.0) (2025-07-23)


### Features

* Implement EquipmentType in UI. Corresponding test updated. ([75af6a9](https://github.com/rad-solutions/webserver/commit/75af6a9e9ec4abc5ba6c316ae5e0f3202eceb85b))

# [1.52.0](https://github.com/rad-solutions/webserver/compare/v1.51.0...v1.52.0) (2025-07-22)


### Features

* Standardize equipment model with EquipmentType ([b78e604](https://github.com/rad-solutions/webserver/commit/b78e60466d11af95814a1e0e06e1272034ab63ef))

# [1.51.0](https://github.com/rad-solutions/webserver/compare/v1.50.0...v1.51.0) (2025-07-22)


### Features

* New labels for process list for internal users. Corresponding test added. ([fc20ffc](https://github.com/rad-solutions/webserver/commit/fc20ffc140a49e06cab0dd26ca4c6a5405f4651c))

# [1.50.0](https://github.com/rad-solutions/webserver/compare/v1.49.0...v1.50.0) (2025-07-22)


### Features

* add detailed logging to PDFStorage for debugging ([143d3d9](https://github.com/rad-solutions/webserver/commit/143d3d959bc510643b9368fba476bcdc757c3b4e))

# [1.49.0](https://github.com/rad-solutions/webserver/compare/v1.48.0...v1.49.0) (2025-07-21)


### Features

* Changed date pickers to match model and added a date picker for the due_date field of the model. ([7ae2ad7](https://github.com/rad-solutions/webserver/commit/7ae2ad72ca22ce5e948428ce4e03e7a1f46a1289))

# [1.48.0](https://github.com/rad-solutions/webserver/compare/v1.47.0...v1.48.0) (2025-07-21)


### Features

* Allow long filenames for report PDFs and add test ([028ad35](https://github.com/rad-solutions/webserver/commit/028ad35a0cdd7ff64516794b87b6ed91234b06f6))

# [1.47.0](https://github.com/rad-solutions/webserver/compare/v1.46.0...v1.47.0) (2025-07-21)


### Features

* Added new graphs on the dashboard for Gerentes. Corresponding test added. ([23ab2dc](https://github.com/rad-solutions/webserver/commit/23ab2dc1eac32a05492201fe9b531b26660d6313))

# [1.46.0](https://github.com/rad-solutions/webserver/compare/v1.45.0...v1.46.0) (2025-07-21)


### Features

* Implementation in the UI of the change in the Process model. Tests revisited and debugged. populate-db command fixed. ([e3ece5d](https://github.com/rad-solutions/webserver/commit/e3ece5db6d78a48d31b9439f132d9842f18bdb44))

# [1.45.0](https://github.com/rad-solutions/webserver/compare/v1.44.0...v1.45.0) (2025-07-18)


### Features

* Equipos_list page improved. Added marking to near-expiration equipment and added a graph of CC by interval time for Gerente users. Corresponding tests added. ([6e7c011](https://github.com/rad-solutions/webserver/commit/6e7c0114b09c14af9d27692b6cac5b2e9c894b37))

# [1.44.0](https://github.com/rad-solutions/webserver/compare/v1.43.1...v1.44.0) (2025-07-18)


### Features

* Changed table labels in report list to make them more clear. ([9c39955](https://github.com/rad-solutions/webserver/commit/9c3995546ac55cec8d81a9d8de031ac2be65a534))

## [1.43.1](https://github.com/rad-solutions/webserver/compare/v1.43.0...v1.43.1) (2025-07-18)


### Bug Fixes

* increase gunicorn timeout ([3b34f5a](https://github.com/rad-solutions/webserver/commit/3b34f5a7d0a2a1928116948641215403f09154d5))
* test ci ([26dd6ee](https://github.com/rad-solutions/webserver/commit/26dd6ee0475b77b07a10289d0f7250b04db84f3c))

# [1.43.0](https://github.com/rad-solutions/webserver/compare/v1.42.0...v1.43.0) (2025-07-17)


### Features

* Add 'En Espera Administrativa' process status ([5a452e6](https://github.com/rad-solutions/webserver/commit/5a452e6fd1744c0d23ce6119ac1c3dcf80b49069))
* Add 'Requiere Corrección' status to Report model ([984a63e](https://github.com/rad-solutions/webserver/commit/984a63e7648935ecf36d064b7c3290958113da21))
* Add 'Requiere Corrección' status to Report model ([a76b675](https://github.com/rad-solutions/webserver/commit/a76b675e536ae84887a64958e166e1b8a0a2f468))
* Fix migrations inconsistency 3 ([6dd6481](https://github.com/rad-solutions/webserver/commit/6dd6481b16c67678a2df254ac8929c55076f81b6))
* User role now showing on the User List. ([1dc7daf](https://github.com/rad-solutions/webserver/commit/1dc7daf32d428d3ae3cb5fd4f70f09323793972f))

# [1.42.0](https://github.com/rad-solutions/webserver/compare/v1.41.0...v1.42.0) (2025-07-17)


### Features

* Fix error report detail crash when no process asociated to it. ([b16aec0](https://github.com/rad-solutions/webserver/commit/b16aec005ba648725baff5f54175b3ed068cff00))

# [1.41.0](https://github.com/rad-solutions/webserver/compare/v1.40.0...v1.41.0) (2025-07-17)


### Features

* Add due_date to ProcessChecklistItem model ([1e838e8](https://github.com/rad-solutions/webserver/commit/1e838e82934a02d1c7bfa2cb3d3fce780d98c619))

# [1.40.0](https://github.com/rad-solutions/webserver/compare/v1.39.0...v1.40.0) (2025-07-16)


### Features

* Fix labels and help text in User Creation Form. ([91594c4](https://github.com/rad-solutions/webserver/commit/91594c4ddbe1ab2f684ab867d6eacd2bff51b183))
* Fix title in process_detail to show correct Process Type String (For example, Calculo de Blindajes instead of calculo_blindajes). ([460ac1a](https://github.com/rad-solutions/webserver/commit/460ac1adb1bde7098c3fda8fa323d4fb6aca01b7))
* Labels on forms now in Spanish and well written. Corresponding tests added. ([229f1a1](https://github.com/rad-solutions/webserver/commit/229f1a15603a80a0c5d1a860be28d600d697afa8))

# [1.39.0](https://github.com/rad-solutions/webserver/compare/v1.38.0...v1.39.0) (2025-07-16)


### Features

* Implement dynamic host configuration for deployments ([2b776dd](https://github.com/rad-solutions/webserver/commit/2b776dd3e77f8ef04e80d4c9ac8411efa99a854f))

# [1.38.0](https://github.com/rad-solutions/webserver/compare/v1.37.0...v1.38.0) (2025-07-15)


### Features

* ProcessCheckList Item field "Status" now showing on UI. ([f7b3f11](https://github.com/rad-solutions/webserver/commit/f7b3f11cc1a3748116b4f9c86b1bda54eba091d5))

# [1.37.0](https://github.com/rad-solutions/webserver/compare/v1.36.0...v1.37.0) (2025-07-15)


### Features

* Change messages for the client in dashboard. Corresponding tests adapted. ([1d835e8](https://github.com/rad-solutions/webserver/commit/1d835e8318d709446fec0f8354f1ed4e6b76f307))

# [1.36.0](https://github.com/rad-solutions/webserver/compare/v1.35.0...v1.36.0) (2025-07-15)


### Features

* Add Razón Social of the Client to the process detail. ([ecb2c9a](https://github.com/rad-solutions/webserver/commit/ecb2c9a5764f55deb97fee8903ecfce3e525a628))

# [1.35.0](https://github.com/rad-solutions/webserver/compare/v1.34.0...v1.35.0) (2025-07-15)


### Features

* Restauración Rama PR # 51 ([b154268](https://github.com/rad-solutions/webserver/commit/b15426822a8e6fa846a36871da5a393e0e4b40da))

# [1.34.0](https://github.com/rad-solutions/webserver/compare/v1.33.0...v1.34.0) (2025-07-15)


### Features

* Implementar seguimiento de estado para ítems de checklist ([4e6441e](https://github.com/rad-solutions/webserver/commit/4e6441e5d7986445eb50ed001739de336da39394))
* pull always policy in docker compose.yaml ([40a5804](https://github.com/rad-solutions/webserver/commit/40a580420ecf23cef417ff4a13bb6c0537b506e2))

# [1.33.0](https://github.com/rad-solutions/webserver/compare/v1.32.0...v1.33.0) (2025-07-14)


### Features

* Restauración Rama a PR # 49 ([e5508f8](https://github.com/rad-solutions/webserver/commit/e5508f881c01d809ce08d3797680ec4c3eb9d01f))

# [1.32.0](https://github.com/rad-solutions/webserver/compare/v1.31.0...v1.32.0) (2025-07-14)


### Bug Fixes

* github actions ([0cb9d1e](https://github.com/rad-solutions/webserver/commit/0cb9d1ed931577d7b307b8bd0946ced958c88b2c))
* github actions ([47524d2](https://github.com/rad-solutions/webserver/commit/47524d298611839aebdb79f06403dab388887435))
* github actions2 ([ece8fce](https://github.com/rad-solutions/webserver/commit/ece8fce4e9481baeca1e5cbe209acebc7c3433f6))
* github actions3 ([956dfeb](https://github.com/rad-solutions/webserver/commit/956dfeb9d1d0d2edbcfff683be1c66dcfee63ff0))


### Features

* Added buttons to the dashboard of internal users. No test changes are needed. ([f35f070](https://github.com/rad-solutions/webserver/commit/f35f0709b860906668227f5c24ae1604bea037c6))
* FIxed saving process and report, now using the save() model function. No need to update or create new tests. ([e5a9965](https://github.com/rad-solutions/webserver/commit/e5a996508b9d10379032e33e20ecf545cc058015))

# [1.31.0](https://github.com/rad-solutions/webserver/compare/v1.30.0...v1.31.0) (2025-07-11)


### Features

* Implementar seguimiento de estado para ítems de checklist ([e2ba73d](https://github.com/rad-solutions/webserver/commit/e2ba73dc9129d4ebe18fa657d031a27c4adef096))

# [1.30.0](https://github.com/rad-solutions/webserver/compare/v1.29.0...v1.30.0) (2025-07-11)


### Features

* Actualizar script populate_db y configuración de Docker ([f1d30c9](https://github.com/rad-solutions/webserver/commit/f1d30c91020e4a34fc14b29edfd2d4829b5ab3e5))

# [1.29.0](https://github.com/rad-solutions/webserver/compare/v1.28.0...v1.29.0) (2025-07-10)


### Features

* Added process progress percentage on process list for a client. Corresponding tests added. ([8c5cff0](https://github.com/rad-solutions/webserver/commit/8c5cff0f51fcd3ba43e4f85478da9f97cb495c6c))

# [1.28.0](https://github.com/rad-solutions/webserver/compare/v1.27.0...v1.28.0) (2025-07-10)


### Features

* Update populate_db script to match recent model changes ([700703c](https://github.com/rad-solutions/webserver/commit/700703c465d12a32093bcc848a9761cba7790366))

# [1.27.0](https://github.com/rad-solutions/webserver/compare/v1.26.0...v1.27.0) (2025-07-10)


### Features

* Fix minor issue with a test. ([40c972b](https://github.com/rad-solutions/webserver/commit/40c972bb32c1d37c1c98ac7ddd6ae1058d33f270))
* Now showing the user that completed a checklist item when retrievieng information after being saved. ([a17b0b2](https://github.com/rad-solutions/webserver/commit/a17b0b23ddf2a82ce201647510ebc67668434f82))
* Updated dashboard cliente to include the new process type and the buttons for the sidebar are now dynamic. Corresponding test added. ([69e4c2e](https://github.com/rad-solutions/webserver/commit/69e4c2ec90a65fb634de9a935190b407c5d38cd6))
* Updated the form and now the process categories are dynamic matching the process type selection. ([6f7b045](https://github.com/rad-solutions/webserver/commit/6f7b0454142bb644642c6bb5825c4484797057fa))

# [1.26.0](https://github.com/rad-solutions/webserver/compare/v1.25.0...v1.26.0) (2025-07-10)


### Features

* Document CI/CD workflow with ECR integration test 6 ([e1ef682](https://github.com/rad-solutions/webserver/commit/e1ef68222c94730877dcf41e7da5cf0b1d330df3))

# [1.25.0](https://github.com/rad-solutions/webserver/compare/v1.24.0...v1.25.0) (2025-07-10)


### Features

* Document CI/CD workflow with ECR integration test 5 ([ba5de11](https://github.com/rad-solutions/webserver/commit/ba5de1148c49327a75e147b8ebfd4c3a01504944))

# [1.24.0](https://github.com/rad-solutions/webserver/compare/v1.23.0...v1.24.0) (2025-07-10)


### Features

* Document CI/CD workflow with ECR integration test 5 ([2a8a396](https://github.com/rad-solutions/webserver/commit/2a8a39606cb0816d173a4f3a5a30acb3b3ef5a7b))

# [1.23.0](https://github.com/rad-solutions/webserver/compare/v1.22.0...v1.23.0) (2025-07-10)


### Features

* Document CI/CD workflow with ECR integration test 4 ([28ba752](https://github.com/rad-solutions/webserver/commit/28ba7520dfeb803ac3456f89689ff69363f32da7))

# [1.22.0](https://github.com/rad-solutions/webserver/compare/v1.21.0...v1.22.0) (2025-07-09)


### Features

* Document CI/CD workflow with ECR integration test 3 ([7d65f78](https://github.com/rad-solutions/webserver/commit/7d65f78a0d059a4476d6700d1651fd0f4613c5d3))

# [1.21.0](https://github.com/rad-solutions/webserver/compare/v1.20.0...v1.21.0) (2025-07-09)


### Features

* Document CI/CD workflow with ECR integration test 2 ([e28b734](https://github.com/rad-solutions/webserver/commit/e28b7342adb90123cb47288485b4c67ba0c97561))

# [1.20.0](https://github.com/rad-solutions/webserver/compare/v1.19.0...v1.20.0) (2025-07-09)


### Features

* Document CI/CD workflow with ECR integration ([a237b47](https://github.com/rad-solutions/webserver/commit/a237b47952eedcb6193effbda09abfcde71cdb9f))

# [1.19.0](https://github.com/rad-solutions/webserver/compare/v1.18.1...v1.19.0) (2025-07-09)


### Features

* Added buttons for process and equipment creation for internal user on process list page. ([d3265d3](https://github.com/rad-solutions/webserver/commit/d3265d39344087a737814c99cf4430ec2d3a2d25))
* Added equipment filters on report list page. Added corresponding tests. ([52a9055](https://github.com/rad-solutions/webserver/commit/52a90559397f4863d30fc924ec12fb0bde139e01))

## [1.18.1](https://github.com/rad-solutions/webserver/compare/v1.18.0...v1.18.1) (2025-07-08)


### Bug Fixes

* Refactor process and checklist logic ([6ed91df](https://github.com/rad-solutions/webserver/commit/6ed91df816aa3c084532705f3d61859c17648a5a))

# [1.18.0](https://github.com/rad-solutions/webserver/compare/v1.17.0...v1.18.0) (2025-07-07)


### Features

* FIxed asc-desc mixup. ([c47769d](https://github.com/rad-solutions/webserver/commit/c47769d2410b4de0e3f6fa12163e922eaf53d497))
* Process List for internal users. Filters and ordering options added. Corresponding tests added. ([698f0c7](https://github.com/rad-solutions/webserver/commit/698f0c7f3cc5ea7bc3a92ec48b1959d55918455e))

# [1.17.0](https://github.com/rad-solutions/webserver/compare/v1.16.0...v1.17.0) (2025-07-04)


### Features

* Added Dashboard for internal users (not gerente). Corresponding tests added. ([7d9a7ca](https://github.com/rad-solutions/webserver/commit/7d9a7caafc204663a4e98cbeab1889e8d0bd2608))

# [1.16.0](https://github.com/rad-solutions/webserver/compare/v1.15.0...v1.16.0) (2025-07-04)


### Features

* Added dashboard for internal user "Gerente". Corresponding test added. ([b749e75](https://github.com/rad-solutions/webserver/commit/b749e753206e7225a69977c1b3addc68e0d1d2ec))
* Added tearDown function to report_history tests to ensure correct test functionality across multiple consecutive runs. ([ae0f469](https://github.com/rad-solutions/webserver/commit/ae0f4694a66fad45a02436ae788075e883c786e1))

# [1.15.0](https://github.com/rad-solutions/webserver/compare/v1.14.0...v1.15.0) (2025-07-02)


### Features

* Now showing ProcessStatusLogs in the process detail page. Corresponding test added. ([443a1b2](https://github.com/rad-solutions/webserver/commit/443a1b22788c222405abef94d1414437df2ad00e))

# [1.14.0](https://github.com/rad-solutions/webserver/compare/v1.13.0...v1.14.0) (2025-06-27)


### Features

* Track report file changes in history ([832d128](https://github.com/rad-solutions/webserver/commit/832d1283c167d1f8e6a07cedc906ba5b1321ca26))

# [1.13.0](https://github.com/rad-solutions/webserver/compare/v1.12.0...v1.13.0) (2025-06-26)


### Features

* Added system for review and approval of a report and a way to add a Process' Anotacion in the same page as the review one. Now showing the Anotaciones asociated to the asociated process of the report. Corresponding test added ([f9e4642](https://github.com/rad-solutions/webserver/commit/f9e464246b7e23e4660dc585d7a54fc9c0e90440))

# [1.12.0](https://github.com/rad-solutions/webserver/compare/v1.11.0...v1.12.0) (2025-06-26)


### Features

* Added UI for Creation and Updating the XRay Tube asociated to an Equipment as well as its history. Corresponding test added. ([10690c0](https://github.com/rad-solutions/webserver/commit/10690c0cf914f6148bd3d4eedc50f3a5fa345cdd))

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

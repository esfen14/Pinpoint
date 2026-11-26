# PinPoint Network Diagnosis System

## Technical Manual

| | |
|---|---|
| Product | PinPoint (Detech-IT / 4D-G2) |
| Document | Technical Manual |
| Version | 0.1 (draft) |
| Status | Draft for owner review, issue #181 |
| Date | 2026-11-15 |
| Audience | Developers, network engineers, system administrators, IT staff and future maintainers |
| Companion | [User Manual](../User_Manual/User_Manual.md) |
| Source of truth | [`spec files/`](../../spec%20files/README.md); this manual summarises it and must not contradict it |

> **Draft notice.** This draft was written from the specifications, the topic
> guides, the model files and configuration in this repository. Installer
> behaviour was read from the separate installer repository
> (`lorraine-pangilinan/PinPoint-Installer`) and partly checked on an ISO install
> and on lab appliances (November 2026). Its maintainer has not yet confirmed it,
> and nothing was checked on a production system. Items still open are listed in
> [Appendix C](14_Appendices.md#appendix-c-still-to-be-confirmed). Diagrams are
> drawn from the code as Mermaid diagrams; the capstone paper's architecture
> figure is redrawn and compared in section 2.7, and the ERD is generated from the
> schema (section 6.3).

### Labelling convention

| Label | Meaning |
|---|---|
| **[V]** Verified | Read from source code, a specification or a recorded lab report in this repository |
| **[A]** Assumption | A reasonable inference not stated in the repository |
| **[R]** Recommended | An improvement that is **not** implemented |
| **TBC** | To Be Confirmed; the information is not available in this repository |

Unlabelled statements in sections 1 to 11 are **[V]**.

Each chapter below is a separate file in this folder. Topic guides for
maintainers are in [`guides/`](guides): [Backup and restore](guides/Backup_and_Restore.md)
and the [Local lab](guides/Local_Lab.md).

---

## Table of contents

1. [Technical system overview](01_Technical_system_overview.md)
2. [Architecture and design](02_Architecture_and_design.md)
3. [Hardware requirements](03_Hardware_requirements.md)
4. [Software requirements](04_Software_requirements.md)
5. [Network requirements and configuration](05_Network_requirements_and_configuration.md)
6. [Database design and management](06_Database_design_and_management.md)
7. [Components and functional modules](07_Components_and_functional_modules.md)
8. [Installation and deployment](08_Installation_and_deployment.md)
9. [System security](09_System_security.md)
10. [Testing and validation](10_Testing_and_validation.md)
11. [Maintenance and troubleshooting](11_Maintenance_and_troubleshooting.md)
12. [Scalability and future enhancements](12_Scalability_and_future_enhancements.md)
13. [Glossary and abbreviations](13_Glossary_and_abbreviations.md)
14. [Appendices](14_Appendices.md)

---

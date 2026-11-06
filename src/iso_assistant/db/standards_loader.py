"""Reference standards catalog loader and SQLite seeder.

Populates ISO/IEC 27001:2022 Clauses 4-10 and the 93 Annex A controls.
Note: Adheres strictly to copyright protection guidelines: contains only
public structural identifiers, standard category titles, and non-copyrighted summaries.
"""

import json
from pathlib import Path

from sqlalchemy.orm import Session

from iso_assistant.config import settings
from iso_assistant.db.models import ISOControl
from iso_assistant.db.repository import ControlRepository
from iso_assistant.utils.logger import get_logger

logger = get_logger(__name__)

# Complete ISO 27001:2022 structural definitions
ISO_27001_2022_DATA: list[dict[str, str]] = [
    # Management System Clauses 4-10
    {
        "id": "Clause.4.1",
        "category": "Clause",
        "theme": "Clause 4: Context of the Organization",
        "title": "Understanding the organization and its context",
        "summary": "Determine external and internal issues relevant to the purpose of the organization and its ISMS.",
        "guidance": "Examine organizational strategy, business environment, legal landscape, and risk tolerance.",
    },
    {
        "id": "Clause.4.2",
        "category": "Clause",
        "theme": "Clause 4: Context of the Organization",
        "title": "Understanding needs and expectations of interested parties",
        "summary": "Identify interested parties relevant to the ISMS and their requirements.",
        "guidance": "Document requirements from customers, regulators, shareholders, and internal stakeholders.",
    },
    {
        "id": "Clause.4.3",
        "category": "Clause",
        "theme": "Clause 4: Context of the Organization",
        "title": "Determining the scope of the ISMS",
        "summary": "Define boundaries and applicability of the Information Security Management System.",
        "guidance": "Formally document ISMS scope covering organizational units, locations, assets, and technologies.",
    },
    {
        "id": "Clause.4.4",
        "category": "Clause",
        "theme": "Clause 4: Context of the Organization",
        "title": "Information security management system",
        "summary": "Establish, implement, maintain and continually improve an ISMS.",
        "guidance": "Ensure ISMS processes and interactions are documented and operational.",
    },
    {
        "id": "Clause.5.1",
        "category": "Clause",
        "theme": "Clause 5: Leadership",
        "title": "Leadership and commitment",
        "summary": "Top management must demonstrate leadership and commitment regarding the ISMS.",
        "guidance": "Ensure security policy and objectives align with business strategy and resources are allocated.",
    },
    {
        "id": "Clause.5.2",
        "category": "Clause",
        "theme": "Clause 5: Leadership",
        "title": "Information security policy",
        "summary": "Establish an information security policy approved by top management.",
        "guidance": "Policy must provide framework for security objectives and commitment to continual improvement.",
    },
    {
        "id": "Clause.5.3",
        "category": "Clause",
        "theme": "Clause 5: Leadership",
        "title": "Organizational roles, responsibilities and authorities",
        "summary": "Assign and communicate information security roles and authorities.",
        "guidance": "Formally designate CISO / security lead, asset owners, and RACI matrices.",
    },
    {
        "id": "Clause.6.1.1",
        "category": "Clause",
        "theme": "Clause 6: Planning",
        "title": "Actions to address risks and opportunities - General",
        "summary": "Plan ISMS actions considering context and interested party requirements.",
        "guidance": "Ensure ISMS can achieve intended outcomes and prevent undesired effects.",
    },
    {
        "id": "Clause.6.1.2",
        "category": "Clause",
        "theme": "Clause 6: Planning",
        "title": "Information security risk assessment",
        "summary": "Define and apply an information security risk assessment process.",
        "guidance": "Establish risk criteria, identify risks associated with CIA loss, and analyze likelihood and impact.",
    },
    {
        "id": "Clause.6.1.3",
        "category": "Clause",
        "theme": "Clause 6: Planning",
        "title": "Information security risk treatment",
        "summary": "Define and apply a risk treatment process and produce Statement of Applicability (SoA).",
        "guidance": "Select appropriate controls, compare against Annex A, and justify inclusions/exclusions.",
    },
    {
        "id": "Clause.6.2",
        "category": "Clause",
        "theme": "Clause 6: Planning",
        "title": "Information security objectives and planning to achieve them",
        "summary": "Establish measurable information security objectives at relevant functions.",
        "guidance": "Define what will be done, what resources are required, who is responsible, and evaluation metrics.",
    },
    {
        "id": "Clause.6.3",
        "category": "Clause",
        "theme": "Clause 6: Planning",
        "title": "Planning of changes",
        "summary": "Determine need for changes to the ISMS and carry them out in a planned manner.",
        "guidance": "Maintain change management records for ISMS scope, policies, and architecture changes.",
    },
    {
        "id": "Clause.7.1",
        "category": "Clause",
        "theme": "Clause 7: Support",
        "title": "Resources",
        "summary": "Determine and provide resources needed for ISMS establishment and maintenance.",
        "guidance": "Budget, personnel, tooling, and infrastructure allocation.",
    },
    {
        "id": "Clause.7.2",
        "category": "Clause",
        "theme": "Clause 7: Support",
        "title": "Competence",
        "summary": "Ensure personnel are competent on the basis of education, training, or experience.",
        "guidance": "Document security qualifications, certifications, and periodic training records.",
    },
    {
        "id": "Clause.7.3",
        "category": "Clause",
        "theme": "Clause 7: Support",
        "title": "Awareness",
        "summary": "Ensure personnel are aware of security policy and their contribution to ISMS effectiveness.",
        "guidance": "Conduct security awareness campaigns, phishing simulations, and policy acknowledgments.",
    },
    {
        "id": "Clause.7.4",
        "category": "Clause",
        "theme": "Clause 7: Support",
        "title": "Communication",
        "summary": "Determine internal and external communications relevant to the ISMS.",
        "guidance": "Define what to communicate, when, with whom, and who communicates.",
    },
    {
        "id": "Clause.7.5",
        "category": "Clause",
        "theme": "Clause 7: Support",
        "title": "Documented information",
        "summary": "Control creation, updating, and distribution of ISMS documentation.",
        "guidance": "Version control, approval workflows, access protection, and retention policies.",
    },
    {
        "id": "Clause.8.1",
        "category": "Clause",
        "theme": "Clause 8: Operation",
        "title": "Operational planning and control",
        "summary": "Plan, implement, and control processes needed to meet information security requirements.",
        "guidance": "Operational procedures, criteria for processes, and control of outsourced processes.",
    },
    {
        "id": "Clause.8.2",
        "category": "Clause",
        "theme": "Clause 8: Operation",
        "title": "Information security risk assessment execution",
        "summary": "Perform information security risk assessments at planned intervals or when significant changes occur.",
        "guidance": "Maintain documented results of recurring risk assessments.",
    },
    {
        "id": "Clause.8.3",
        "category": "Clause",
        "theme": "Clause 8: Operation",
        "title": "Information security risk treatment execution",
        "summary": "Implement the information security risk treatment plan.",
        "guidance": "Retain documented evidence of risk treatment implementation and residual risk sign-offs.",
    },
    {
        "id": "Clause.9.1",
        "category": "Clause",
        "theme": "Clause 9: Performance Evaluation",
        "title": "Monitoring, measurement, analysis and evaluation",
        "summary": "Evaluate information security performance and ISMS effectiveness.",
        "guidance": "Define security metrics, KPIs, measurement frequencies, and analysis methodologies.",
    },
    {
        "id": "Clause.9.2",
        "category": "Clause",
        "theme": "Clause 9: Performance Evaluation",
        "title": "Internal audit",
        "summary": "Conduct internal audits at planned intervals to verify ISMS conformity.",
        "guidance": "Audit program, independent auditor selection, audit reports, and corrective tracking.",
    },
    {
        "id": "Clause.9.3",
        "category": "Clause",
        "theme": "Clause 9: Performance Evaluation",
        "title": "Management review",
        "summary": "Top management must review the ISMS at planned intervals.",
        "guidance": "Review inputs: audit results, risk assessments, metrics, status of actions from prior reviews.",
    },
    {
        "id": "Clause.10.1",
        "category": "Clause",
        "theme": "Clause 10: Improvement",
        "title": "Continual improvement",
        "summary": "Continually improve suitability, adequacy, and effectiveness of the ISMS.",
        "guidance": "Track security enhancements, lessons learned, and maturity evolution.",
    },
    {
        "id": "Clause.10.2",
        "category": "Clause",
        "theme": "Clause 10: Improvement",
        "title": "Nonconformity and corrective action",
        "summary": "React to nonconformities, take corrective action, and review effectiveness.",
        "guidance": "Maintain corrective action records, root-cause analyses, and re-evaluation outcomes.",
    },
    # Annex A - A.5 Organizational Controls (37 Controls)
    {"id": "A.5.1", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Policies for information security", "summary": "Information security policy and topic-specific policies must be defined, approved, published, and reviewed.", "guidance": "Ensure regular annual review and management approval."},
    {"id": "A.5.2", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Information security roles and responsibilities", "summary": "Information security roles and responsibilities must be defined and allocated.", "guidance": "Document responsibilities in job descriptions and RACI charts."},
    {"id": "A.5.3", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Segregation of duties", "summary": "Conflicting duties and conflicting areas of responsibility must be segregated.", "guidance": "Prevent single individuals from initiating, approving, and executing critical actions."},
    {"id": "A.5.4", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Management responsibilities", "summary": "Management must require personnel to apply security in accordance with established policies.", "guidance": "Ensure security compliance is part of employee evaluation."},
    {"id": "A.5.5", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Contact with authorities", "summary": "Appropriate contacts with relevant authorities must be maintained.", "guidance": "Maintain contact list for law enforcement, regulators, and emergency services."},
    {"id": "A.5.6", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Contact with special interest groups", "summary": "Contacts with special interest groups or security forums must be maintained.", "guidance": "Participate in ISACs, CERTs, or professional security organizations."},
    {"id": "A.5.7", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Threat intelligence", "summary": "Information relating to information security threats must be collected and analyzed.", "guidance": "Ingest vulnerability feeds, threat advisories, and industry alerts."},
    {"id": "A.5.8", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Information security in project management", "summary": "Information security must be integrated into project management methodologies.", "guidance": "Include security milestone reviews and threat modeling in project gates."},
    {"id": "A.5.9", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Inventory of information and other associated assets", "summary": "An inventory of information and other associated assets must be developed and maintained.", "guidance": "Identify asset owners, classifications, and storage locations."},
    {"id": "A.5.10", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Acceptable use of information and other associated assets", "summary": "Rules for acceptable use of assets and information must be defined and documented.", "guidance": "Publish acceptable use policies signed by all personnel."},
    {"id": "A.5.11", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Return of assets", "summary": "Personnel and interested parties must return all organizational assets upon change or termination.", "guidance": "Formal offboarding checklist covering laptops, access tokens, and documents."},
    {"id": "A.5.12", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Classification of information", "summary": "Information must be classified in accordance with security needs based on CIA.", "guidance": "Establish classification tiers (e.g., Public, Internal, Confidential, Restricted)."},
    {"id": "A.5.13", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Labelling of information", "summary": "Procedures for information labelling must be developed and implemented.", "guidance": "Automate or mandate digital tags and header/footer classification markings."},
    {"id": "A.5.14", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Information transfer", "summary": "Information transfer rules, procedures, and agreements must be in place.", "guidance": "Enforce TLS encryption, SFTP, and secure email transfer protocols."},
    {"id": "A.5.15", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Access control", "summary": "Rules to control physical and logical access to information and assets must be established.", "guidance": "Base access on business needs, least privilege, and role-based policies."},
    {"id": "A.5.16", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Identity management", "summary": "The full lifecycle of identities must be managed.", "guidance": "Unique user IDs, formal identity verification, and deprovisioning."},
    {"id": "A.5.17", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Authentication information", "summary": "Allocation and management of authentication info must be controlled by a formal process.", "guidance": "Password complexity, MFA requirements, and secure secrets management."},
    {"id": "A.5.18", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Access rights", "summary": "Access rights to information and assets must be provisioned, reviewed, and modified.", "guidance": "Conduct quarterly access reviews and immediate revocation upon role transfer."},
    {"id": "A.5.19", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Information security in supplier relationships", "summary": "Processes and procedures must be established to manage supplier security risks.", "guidance": "Vendor risk assessments, third-party questionnaires, and security requirements."},
    {"id": "A.5.20", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Addressing information security within supplier agreements", "summary": "Relevant information security requirements must be established with each supplier.", "guidance": "Include security covenants, audit rights, and breach notification clauses in SLAs."},
    {"id": "A.5.21", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Managing information security in the ICT supply chain", "summary": "Processes must be established to manage security risks associated with the ICT supply chain.", "guidance": "Assess component provenance, open-source software dependencies, and hardware authenticity."},
    {"id": "A.5.22", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Monitoring, review and change management of supplier services", "summary": "Organizations must regularly monitor, review, and evaluate supplier service delivery.", "guidance": "Review SOC 2 / ISO certifications and service performance audits."},
    {"id": "A.5.23", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Information security for use of cloud services", "summary": "Processes for acquisition, use, management, and exit from cloud services must be established.", "guidance": "Define cloud shared responsibility models and data residency requirements."},
    {"id": "A.5.24", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Information security incident management planning and preparation", "summary": "Plan and prepare for managing security incidents by defining procedures and roles.", "guidance": "Incident response plan, escalation matrix, and IR team readiness."},
    {"id": "A.5.25", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Assessment and decision on information security events", "summary": "Assess security events and decide if they are to be categorized as incidents.", "guidance": "Triage playbooks, severity classification matrix."},
    {"id": "A.5.26", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Response to information security incidents", "summary": "Respond to information security incidents in accordance with documented procedures.", "guidance": "Containment, eradication, recovery, and communication protocols."},
    {"id": "A.5.27", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Learning from information security incidents", "summary": "Knowledge gained from security incidents must be used to strengthen controls.", "guidance": "Formal post-incident review (post-mortem) and action items tracking."},
    {"id": "A.5.28", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Collection of evidence", "summary": "Establish procedures for identification, collection, acquisition, and preservation of evidence.", "guidance": "Forensic chain of custody and tamper-evident preservation."},
    {"id": "A.5.29", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Information security during disruption", "summary": "Plan how to maintain security at an appropriate level during disruptions.", "guidance": "Disaster recovery plans and emergency operational security controls."},
    {"id": "A.5.30", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "ICT readiness for business continuity", "summary": "ICT readiness must be planned, implemented, maintained, and tested based on business continuity objectives.", "guidance": "RTO / RPO requirements and annual disaster recovery failover tests."},
    {"id": "A.5.31", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Legal, statutory, regulatory and contractual requirements", "summary": "Identify and document compliance requirements applicable to information security.", "guidance": "Maintain legal register (GDPR, HIPAA, local cybersecurity laws)."},
    {"id": "A.5.32", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Intellectual property rights", "summary": "Implement appropriate procedures to protect intellectual property rights.", "guidance": "Software license compliance, copyright notices, and patent protection."},
    {"id": "A.5.33", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Protection of records", "summary": "Protect records from loss, destruction, falsification, and unauthorized access.", "guidance": "Record retention schedules and cryptographic archive integrity."},
    {"id": "A.5.34", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Privacy and protection of PII", "summary": "Ensure privacy and protection of personally identifiable information as per laws and contracts.", "guidance": "Privacy impact assessments (PIA), consent management, and data subject rights."},
    {"id": "A.5.35", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Independent review of information security", "summary": "Independent review of the organization's approach to information security must be conducted.", "guidance": "External audits, third-party security assessments."},
    {"id": "A.5.36", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Compliance with policies and standards for information security", "summary": "Managers must regularly review compliance of information processing with security policies.", "guidance": "Technical compliance reviews, regular managerial checks."},
    {"id": "A.5.37", "category": "Annex A", "theme": "Organizational Controls (A.5)", "title": "Documented operating procedures", "summary": "Operating procedures for information processing facilities must be documented and available.", "guidance": "Standard operating procedures (SOPs) for routine IT and security tasks."},

    # Annex A - A.6 People Controls (8 Controls)
    {"id": "A.6.1", "category": "Annex A", "theme": "People Controls (A.6)", "title": "Screening", "summary": "Background verification checks on candidates must be carried out proportional to business ethics and risks.", "guidance": "Pre-employment verification, criminal and reference checks."},
    {"id": "A.6.2", "category": "Annex A", "theme": "People Controls (A.6)", "title": "Terms and conditions of employment", "summary": "Employment agreements must state employee and organizational security responsibilities.", "guidance": "Contractual security clauses and disciplinary policy references."},
    {"id": "A.6.3", "category": "Annex A", "theme": "People Controls (A.6)", "title": "Information security awareness, education and training", "summary": "Personnel must receive appropriate security awareness training and regular updates.", "guidance": "Mandatory onboarding and annual refresher training modules."},
    {"id": "A.6.4", "category": "Annex A", "theme": "People Controls (A.6)", "title": "Disciplinary process", "summary": "A formal disciplinary process must be in place for security breaches.", "guidance": "Documented and communicated disciplinary policy with graduated sanctions."},
    {"id": "A.6.5", "category": "Annex A", "theme": "People Controls (A.6)", "title": "Responsibilities after termination or change of employment", "summary": "Information security responsibilities that remain valid after termination must be defined.", "guidance": "Non-disclosure obligations and return of confidential assets."},
    {"id": "A.6.6", "category": "Annex A", "theme": "People Controls (A.6)", "title": "Confidentiality or non-disclosure agreements", "summary": "Confidentiality agreements reflecting organizational needs must be identified and signed.", "guidance": "NDAs signed by employees, contractors, and partners."},
    {"id": "A.6.7", "category": "Annex A", "theme": "People Controls (A.6)", "title": "Remote working", "summary": "Security measures must be implemented when personnel work remotely.", "guidance": "VPN, disk encryption, remote wiping capability, and home office security."},
    {"id": "A.6.8", "category": "Annex A", "theme": "People Controls (A.6)", "title": "Information security event reporting", "summary": "Personnel must report observed or suspected security events through designated channels.", "guidance": "Accessible reporting mechanism and encouragement of timely reporting without fear of blame."},

    # Annex A - A.7 Physical Controls (14 Controls)
    {"id": "A.7.1", "category": "Annex A", "theme": "Physical Controls (A.7)", "title": "Physical security perimeters", "summary": "Security perimeters must be defined and used to protect areas that contain sensitive information.", "guidance": "Fences, entry gates, badge-controlled access doors."},
    {"id": "A.7.2", "category": "Annex A", "theme": "Physical Controls (A.7)", "title": "Physical entry", "summary": "Secure areas must be protected by appropriate entry controls and access points.", "guidance": "Badge readers, visitor logs, visitor escorts."},
    {"id": "A.7.3", "category": "Annex A", "theme": "Physical Controls (A.7)", "title": "Securing offices, rooms and facilities", "summary": "Physical security for offices, rooms and facilities must be designed and applied.", "guidance": "Keycard access, lockable server rooms, window locks."},
    {"id": "A.7.4", "category": "Annex A", "theme": "Physical Controls (A.7)", "title": "Physical security monitoring", "summary": "Premises must be continuously monitored for unauthorized physical access.", "guidance": "CCTV cameras, intrusion detection alarms, security guard patrols."},
    {"id": "A.7.5", "category": "Annex A", "theme": "Physical Controls (A.7)", "title": "Protecting against physical and environmental threats", "summary": "Protection against fire, flood, earthquake, and other disasters must be designed and applied.", "guidance": "Fire suppression systems, water sensors, climate control."},
    {"id": "A.7.6", "category": "Annex A", "theme": "Physical Controls (A.7)", "title": "Working in secure areas", "summary": "Security measures for working in secure areas must be designed and applied.", "guidance": "No photography/recording devices, clean desk enforcement."},
    {"id": "A.7.7", "category": "Annex A", "theme": "Physical Controls (A.7)", "title": "Clear desk and clear screen", "summary": "Clear desk rules for papers and clear screen rules for information processing must be defined.", "guidance": "Lock workstations when leaving (Win+L), lock paper files in cabinets."},
    {"id": "A.7.8", "category": "Annex A", "theme": "Physical Controls (A.7)", "title": "Equipment siting and protection", "summary": "Equipment must be sited and protected to reduce risks from environmental threats and unauthorized access.", "guidance": "Protected server racks, shielded screens from public view."},
    {"id": "A.7.9", "category": "Annex A", "theme": "Physical Controls (A.7)", "title": "Security of assets off-premises", "summary": "Off-site assets must be protected considering the different risks of working outside premises.", "guidance": "Full disk encryption on laptops, asset tracking."},
    {"id": "A.7.10", "category": "Annex A", "theme": "Physical Controls (A.7)", "title": "Storage media", "summary": "Storage media must be managed through lifecycle of acquisition, use, transportation, and disposal.", "guidance": "Encrypted USBs, authorized media only, secure transport."},
    {"id": "A.7.11", "category": "Annex A", "theme": "Physical Controls (A.7)", "title": "Supporting utilities", "summary": "Information processing facilities must be protected from power failures and other disruptions.", "guidance": "UPS backup power, emergency generators, dual power feeds."},
    {"id": "A.7.12", "category": "Annex A", "theme": "Physical Controls (A.7)", "title": "Cabling security", "summary": "Cables carrying power, data or supporting information services must be protected from interception or damage.", "guidance": "Conduit routing, structured patch panels, inspection for wiretaps."},
    {"id": "A.7.13", "category": "Annex A", "theme": "Physical Controls (A.7)", "title": "Equipment maintenance", "summary": "Equipment must be correctly maintained to ensure integrity and availability.", "guidance": "Scheduled vendor maintenance, authorized technician escort."},
    {"id": "A.7.14", "category": "Annex A", "theme": "Physical Controls (A.7)", "title": "Secure disposal or re-use of equipment", "summary": "Items containing storage media must be verified to ensure sensitive data has been destroyed or overwritten.", "guidance": "NIST SP 800-88 sanitization certificates, physical degaussing/shredding."},

    # Annex A - A.8 Technological Controls (34 Controls)
    {"id": "A.8.1", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "User endpoint devices", "summary": "Information stored on, processed by, or accessible via user endpoint devices must be protected.", "guidance": "MDM / EDR management, disk encryption, remote wipe."},
    {"id": "A.8.2", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Privileged access rights", "summary": "Allocation and use of privileged access rights must be restricted and managed.", "guidance": "Dedicated admin accounts, PAM solutions, session recording, MFA."},
    {"id": "A.8.3", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Information access restriction", "summary": "Access to information and other associated assets must be restricted according to established access control policy.", "guidance": "ACLs, RBAC, network share permissions."},
    {"id": "A.8.4", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Access to source code", "summary": "Read and write access to source code, development tools, and software libraries must be managed.", "guidance": "Git repo permissions, protected branches, mandatory pull request approvals."},
    {"id": "A.8.5", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Secure authentication", "summary": "Secure authentication technologies and procedures must be established.", "guidance": "Hardware MFA, FIDO2 / WebAuthn, risk-based adaptive authentication."},
    {"id": "A.8.6", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Capacity management", "summary": "The use of resources must be monitored and adjusted in line with capacity requirements.", "guidance": "CPU/RAM/storage monitoring, auto-scaling, capacity planning."},
    {"id": "A.8.7", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Protection against malware", "summary": "Protection against malware must be implemented and supported by appropriate user awareness.", "guidance": "Anti-virus/EDR agents with real-time scanning, automatic signature updates."},
    {"id": "A.8.8", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Management of technical vulnerabilities", "summary": "Information about technical vulnerabilities must be obtained, evaluated, and addressed.", "guidance": "Vulnerability scanning, prioritized patch management SLAs."},
    {"id": "A.8.9", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Configuration management", "summary": "Configurations of hardware, software, services, and networks must be established, documented, and monitored.", "guidance": "Hardening baselines (CIS Benchmarks), Infrastructure as Code."},
    {"id": "A.8.10", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Information deletion", "summary": "Information stored in information systems must be deleted when no longer required.", "guidance": "Automated data lifecycle policies, secure file shredding."},
    {"id": "A.8.11", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Data masking", "summary": "Data masking must be used in accordance with access control policy and legal requirements.", "guidance": "Pseudonymization, tokenization, dynamic database masking for non-prod."},
    {"id": "A.8.12", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Data leakage prevention", "summary": "Data leakage prevention measures must be applied to systems, networks, and endpoint devices.", "guidance": "Endpoint DLP, email outbound inspection, cloud access security broker (CASB)."},
    {"id": "A.8.13", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Information backup", "summary": "Backup copies of information, software, and systems must be maintained and regularly tested.", "guidance": "3-2-1 backup rule, immutable/air-gapped backups, periodic restoration drills."},
    {"id": "A.8.14", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Redundancy of information processing facilities", "summary": "Information processing facilities must be implemented with redundancy to meet availability requirements.", "guidance": "High-availability clustering, multi-region failover, load balancing."},
    {"id": "A.8.15", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Logging", "summary": "Logs that record activities, exceptions, faults, and other relevant events must be produced, stored, and protected.", "guidance": "Centralized SIEM, log retention policies, write-once storage protection."},
    {"id": "A.8.16", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Monitoring activities", "summary": "Networks, systems, and applications must be monitored for anomalous behavior.", "guidance": "SOC monitoring, IDS/IPS, automated security alert notifications."},
    {"id": "A.8.17", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Clock synchronization", "summary": "The clocks of information processing systems must be synchronized to approved time sources.", "guidance": "NTP time synchronization with authenticated stratum-1 reference servers."},
    {"id": "A.8.18", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Use of privileged utility programs", "summary": "The use of utility programs that might override controls must be restricted and tightly controlled.", "guidance": "Whitelist utility binaries, monitor root shell access."},
    {"id": "A.8.19", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Installation of software on operational systems", "summary": "Procedures and measures must be implemented to securely manage software installation on operational systems.", "guidance": "Application whitelisting, remove local admin installation rights."},
    {"id": "A.8.20", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Networks security", "summary": "Networks and network devices must be secured, managed, and controlled to protect information.", "guidance": "Next-gen firewalls, VPNs, WAF, secure routing protocols."},
    {"id": "A.8.21", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Security of network services", "summary": "Security mechanisms, service levels, and service requirements of network services must be identified.", "guidance": "Service level agreements with ISPs and cloud network providers."},
    {"id": "A.8.22", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Segregation of networks", "summary": "Groups of information services, users, and systems must be segregated on networks.", "guidance": "VLANs, DMZs, microsegmentation, zero-trust network access (ZTNA)."},
    {"id": "A.8.23", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Web filtering", "summary": "Access to external websites must be managed to reduce exposure to malicious content.", "guidance": "DNS filtering, web proxy URL categorization, blocking command-and-control domains."},
    {"id": "A.8.24", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Use of cryptography", "summary": "Rules for the effective use of cryptography, including cryptographic key management, must be defined.", "guidance": "AES-256 for data at rest, TLS 1.3 for data in transit, automated key rotation in KMS."},
    {"id": "A.8.25", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Secure development life cycle", "summary": "Rules for the secure development of software and systems must be established and applied.", "guidance": "DevSecOps pipelines, automated SAST/DAST scans, secure architecture reviews."},
    {"id": "A.8.26", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Application security requirements", "summary": "Information security requirements must be identified and addressed when developing or acquiring applications.", "guidance": "Input validation, secure session management, transaction integrity."},
    {"id": "A.8.27", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Secure system architecture and engineering principles", "summary": "Principles for engineering secure systems must be established, documented, maintained, and applied.", "guidance": "Zero Trust, defense-in-depth, least privilege architecture."},
    {"id": "A.8.28", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Secure coding", "summary": "Secure coding principles must be applied to software development.", "guidance": "OWASP Top 10 prevention, code review checklists, package lockfiles."},
    {"id": "A.8.29", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Security testing in development and acceptance", "summary": "Security testing processes must be defined and implemented in the development life cycle.", "guidance": "Penetration testing, fuzzing, acceptance testing before release."},
    {"id": "A.8.30", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Outsourced development", "summary": "The organization must direct, monitor, and review outsourced system development.", "guidance": "Security requirements in contracts, escrow, external code audit."},
    {"id": "A.8.31", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Separation of development, test and production environments", "summary": "Development, testing, and production environments must be separated and secured.", "guidance": "Isolated VPCs/subscriptions, no production data in dev/test."},
    {"id": "A.8.32", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Change management", "summary": "Changes to information processing facilities and systems must be subject to change management procedures.", "guidance": "Change Advisory Board (CAB), rollback plans, emergency change approvals."},
    {"id": "A.8.33", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Test information", "summary": "Test information must be appropriately selected, secured, and controlled.", "guidance": "Synthetic or sanitized data only; no unmasked production PII in test environments."},
    {"id": "A.8.34", "category": "Annex A", "theme": "Technological Controls (A.8)", "title": "Protection of information systems during audit testing", "summary": "Audit tests and other assurance activities involving operational systems must be planned and agreed.", "guidance": "Off-peak scheduling, read-only audit roles, approval before automated vulnerability scans."},
]


def export_standards_json(output_path: Path | None = None) -> Path:
    """Exports the structural ISO 27001:2022 dataset to a JSON file."""
    path = output_path or (settings.standards_dir / "iso27001_2022.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ISO_27001_2022_DATA, f, indent=2)
    logger.info("Exported %d ISO 27001:2022 controls to %s", len(ISO_27001_2022_DATA), path)
    return path


def seed_database_standards(db: Session) -> int:
    """Seeds the SQLite database with baseline ISO 27001:2022 controls if not already loaded."""
    existing_count = ControlRepository.count_controls(db)
    if existing_count >= len(ISO_27001_2022_DATA):
        logger.info("Database already contains %d baseline controls. Skipping seeding.", existing_count)
        return existing_count

    controls = [
        ISOControl(
            id=item["id"],
            category=item["category"],
            theme=item["theme"],
            title=item["title"],
            summary=item["summary"],
            guidance=item["guidance"],
        )
        for item in ISO_27001_2022_DATA
    ]
    ControlRepository.bulk_insert_controls(db, controls)
    logger.info("Successfully seeded %d baseline controls into SQLite database.", len(controls))
    return len(controls)

# ResumeLens Professional Profiles

## 1. Purpose

This document defines the professional profiles supported by ResumeLens and specifies the qualifications used to characterize each profile

The profile definitions provide the basis for the qualification normalization and pattern recognition stages of the ResumeLens pipeline.
  They define the qualification categories and representative technologies that will later be used to construct the finite automata for candidate classification.

ResumeLens supports the following four professional profiles:

- Full Stack Developer
- Machine Learning Engineer
- DevOps Engineer
- Data Engineer

The Full Stack Developer and Machine Learning Engineer profiles are based on the reference profiles provided in the integrative task. The DevOps Engineer and Data Engineer profiles are additional profiles selected by the project team, as required by the task

The same ResumeLens processing pipeline is used for all four profiles. The profile-specific qualifications are separate from the general extraction, normalization, and classification logic.

## 2. Full Stack Developer

The Full Stack Developer profile represents candidates who work with both
client-side and server-side components of software applications. The profile
includes qualifications related to user interfaces, backend services, APIs,
database access, and software integration.

### 2.1 Core Qualifications

The Integrative Task defines the following qualifications for the Full Stack
Developer profile:

| Category | Qualifications |
|---|---|
| Programming Languages | JavaScript, TypeScript |
| Frontend | React, Angular, Vue |
| Backend | Node.js, Django, Spring Boot, or similar backend technology |
| Databases | SQL, NoSQL |
| APIs | REST APIs |
| Version Control | Git |

### 2.2 Supporting Qualifications

Supporting qualifications are additional technologies or tools related to
full-stack web development. These qualifications are not considered part of
the core reference qualifications and may provide additional evidence when
classifying a candidate.

Examples include additional frontend frameworks, backend technologies,
database technologies, and web development tools.

## 3. Machine Learning Engineer

The Machine Learning Engineer profile represents candidates who work with
machine learning technologies, data processing tools, and the development of
machine learning models.

### 3.1 Core Qualifications

The following qualifications are used to characterize the Machine Learning
Engineer profile, based on the reference qualifications provided in the
Integrative Task:

- Python
- Pandas or NumPy
- Scikit-learn
- TensorFlow or PyTorch
- Machine-learning model development
- SQL
- Git

### 3.2 Supporting Qualifications

Supporting qualifications are additional technologies or tools related to
machine learning and data processing. These qualifications are not considered
part of the core reference qualifications and may provide additional evidence
when classifying a candidate.

Examples include additional machine learning libraries, data processing
technologies, model development tools, and other technologies related to
machine learning workflow

## 4. DevOps Engineer

The DevOps Engineer profile represents candidates who work with software
delivery, infrastructure, deployment automation, cloud environments, and
operational technologies.

### 4.1 Core Qualifications

The following qualifications are proposed by the project team to characterize
the DevOps Engineer profile:

- Docker or a similar containerization technology
- AWS, Azure, or Google Cloud
- Jenkins, GitHub Actions, or GitLab CI/CD
- Terraform or Ansible
- Git

### 4.2 Supporting Qualifications

Supporting qualifications are additional technologies and tools commonly
associated with DevOps workflows. These qualifications are not considered
part of the core qualifications and may provide additional evidence when
classifying a candidate.

Examples include:

- Kubernetes
- Linux
- Prometheus
- Grafana
- Other cloud and infrastructure technologies

## 5. Data Engineer

The Data Engineer profile represents candidates who work with data collection,
processing, transformation, storage, and data pipeline development.

### 5.1 Core Qualifications

The following qualifications are proposed by the project team to characterize
the Data Engineer profile:

- SQL
- Apache Airflow or a similar data pipeline orchestration technology
- Apache Spark or a similar data processing technology
- PostgreSQL, MySQL, or another database technology
- Databricks or another data storage and processing platform

### 5.2 Supporting Qualifications

Supporting qualifications are additional technologies and tools commonly
associated with data engineering workflows. These qualifications are not
considered part of the core qualifications and may provide additional
evidence when classifying a candidate.

Examples include:

- Python
- Apache Kafka
- MongoDB
- Hadoop
- Other data processing and storage technologies

## 6. Qualification Categories 

ResumeLens organizes extracted qualifications into general categories that
are shared across all supported professional profiles. These categories
provide a common structure for the extraction, normalization, and
classification stages.

The main qualification categories are:

- Programming Languages
- Frameworks and Libraries
- Databases
- Tools and Technologies
- Cloud and Infrastructure
- Machine Learning and Data Technologies
- Version Control
- APIs and Software Development Technologies
- Academic Qualifications
- Professional Experience
- Other Relevant Qualifications

These categories are not specific to a single professional profile.
Different profiles may use different subsets of these categories depending
on their characteristic qualifications.

For example, Python is classified as a Programming Language, React as a
Framework or Library, PostgreSQL as a Database, and Git as a Version Control
technology. These categories allow the system to organize qualifications
consistently before they are used in the profile recognition stage.

## 7. Profile Recognition Principles

ResumeLens classifies candidates by comparing the normalized qualifications
extracted from their resumes with the qualification patterns defined for each
professional profile.

The classification process is based on the presence of relevant
qualifications and combinations of qualifications associated with each
profile. The same recognition mechanism is applied to all four supported
profiles.

The professional profiles are characterized by different combinations of
qualification categories and technologies:

- Full Stack Developer: focuses on frontend and backend development,
  databases, APIs, and version control.
- Machine Learning Engineer: focuses on programming for machine learning,
  data processing, machine learning frameworks, model development, databases,
  and version control.
- DevOps Engineer: focuses on software delivery, infrastructure,
  containerization, cloud environments, and automation.
- Data Engineer: focuses on data processing, data pipelines, ETL or ELT,
  databases, and data storage technologies.

Qualifications are normalized before the recognition process so that
equivalent representations are treated as the same qualification. For
example, different representations of a technology can be mapped to a single
canonical form before being evaluated against a profile.

The specific qualification patterns and acceptance conditions used for
profile recognition are defined separately in the formalization and
classification stages of the project.

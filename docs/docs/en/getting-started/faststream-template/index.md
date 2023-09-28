# FastStream Template

[FastStream Template](https://github.com/airtai/faststream-template/tree/main) is a versatile repository that provides a solid foundation for your Python projects. It comes with a basic application, testing infrastructure, linting scripts, and various development tools to kickstart your development process. Whether you're building a new application from scratch or want to enhance an existing one, this template will save you time and help you maintain high code quality.

## Features

* **Basic Application**: [FastStream Template](https://github.com/airtai/faststream-template/tree/main) includes a basic Python application as a starting point for your project. You can easily replace it with your own code.

* **Testing Framework**: We've set up [`pytest`](https://pytest.org/) for running unit tests. Write your tests in the tests directory and use the provided workflow for automated testing.

* **Linting**: Keep your code clean and consistent with linting tools. The repository includes linting scripts and configurations for [`mypy`](https://mypy.readthedocs.io/en/stable/), [`black`](https://github.com/psf/black), [`ruff`](https://github.com/astral-sh/ruff) and [`bandit`](https://bandit.readthedocs.io/en/latest/)

* **Docker Support**: The included Dockerfile allows you to containerize your [`FastStream`](https://github.com/airtai/faststream) application. Build and run your application in a containerized environment with ease.

* **Dependency Management**: All application requirements and development dependencies are specified in the `pyproject.toml` file. This includes not only your project's dependencies but also configurations for various tools like [`pytest`](https://pytest.org/), [`mypy`](https://mypy.readthedocs.io/en/stable/), [`black`](https://github.com/psf/black), [`ruff`](https://github.com/astral-sh/ruff), and [`bandit`](https://bandit.readthedocs.io/en/latest/).

* **Continuous Integration (CI)**: [FastStream Template](https://github.com/airtai/faststream-template/tree/main) comes with three [GitHub Actions](https://github.com/features/actions) workflows under the `.github/workflows` directory:

  1. **Static Analysis and Testing**: This workflow consists of two jobs. The first job runs static analysis tools ([`mypy`](https://mypy.readthedocs.io/en/stable/) and [`bandit`](https://bandit.readthedocs.io/en/latest/)) to check your code for potential issues. If successful, the second job runs [`pytest`](https://pytest.org/) to execute your test suite.

  2. **Docker Build and Push**: This workflow automates the process of building a [`Docker`](https://www.docker.com/) image for your [`FastStream`](https://github.com/airtai/faststream) application and pushing it to the [GitHub Container Registry](https://ghcr.io).

  3. **AsyncAPI Documentation**: The third workflow builds [`AsyncAPI`](https://www.asyncapi.com/) documentation for your [`FastStream`](https://github.com/airtai/faststream) application and deploys it to [GitHub Pages](https://pages.github.com/). This is useful for documenting your API and making it accessible to others.

## Getting Started

1. **Clone the Repository**: Create your own repo based from the template and Start by cloning this repository to your local machine.
   ```bash
   git clone https://github.com/your-username/faststream-template.git
   cd faststream-template
   ```

2. **Install Dependencies**: Use `pip` to install project dependencies defined in `pyproject.toml`
   ```bash
   pip install -e ".[dev]"
   ```

3. **Customize the Application**: Replace the basic application in the `app` directory with your own code.

4. **Run Tests**: Execute the [`pytest`](https://pytest.org/) suite to run your tests.
   ```bash
   pytest
   ```

5. **Lint Your Code**: Ensure your code adheres to linting standards.
   ```bash
   ./scripts/lint.sh
   ```

6. **Static Analysis and Security Checks**: Run [`mypy`](https://mypy.readthedocs.io/en/stable/) and [`bandit`](https://bandit.readthedocs.io/en/latest/) to perform static analysis and security checks on your code.
   ```bash
   ./scripts/static-analysis.sh
   ```

7. **Dockerize Your Application**: If you want to containerize your application, use the provided `Dockerfile` to build a [`Docker`](https://www.docker.com/) image.
   ```bash
   docker build -t my-faststream-app .
   ```

8. **Push to GitHub**: Commit your changes and push them to your GitHub repository.

9. **GitHub Actions**: The CI workflows are automatically triggered on pushes to the repository. Check the [GitHub Actions](https://github.com/features/actions) tab for build and deployment status.

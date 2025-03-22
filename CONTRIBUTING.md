# Contributing to Forge's DevOps MCP Servers

Thank you for your interest in contributing to Forge's DevOps MCP Servers! This repository is a compilation of DevOps MCP servers designed to help the community deploy, manage, and improve MCP-based solutions. Your contributions—whether adding a new server, refining an existing one, or enhancing documentation—are highly appreciated.

## Table of Contents
- [Types of Contributions](#types-of-contributions)
- [Getting Started](#getting-started)
- [Development Guidelines](#development-guidelines)
- [Contribution Workflow](#contribution-workflow)
- [Pull Request Process](#pull-request-process)
- [Community Guidelines](#community-guidelines)

## Types of Contributions

### 1. New DevOps MCP Servers
We welcome new DevOps MCP server implementations that extend the capabilities of MCP in a secure, reliable manner.

**Guidelines:**
- Verify that your server provides unique functionality or improvements over existing solutions
- Follow security best practices from the MCP documentation
- Ensure your implementation is well-tested and documented
- Add your server reference to the repository's index (maintain alphabetical order)

### 2. Improvements to Existing Servers
Enhancements that improve reliability, performance, security, or usability are always welcome.

**Types of Improvements:**
- Bug fixes and error handling
- Performance and efficiency enhancements
- New features or integrations
- Security updates and hardening
- Test coverage improvements

### 3. Documentation
Clear and comprehensive documentation is vital for a successful project.

**Areas to Contribute:**
- Updating and clarifying instructions
- Adding examples and troubleshooting guides
- Correcting typos and formatting issues
- Enhancing setup instructions
- Creating or improving tutorials

## Getting Started

To contribute, please follow these steps:

1. **Fork the Repository:** Click the "Fork" button at the top right of the repository page
2. **Clone Your Fork:**
   ```bash
   git clone https://github.com/your-username/devops-mcp-servers.git
   cd devops-mcp-servers
   ```
3. **Add the Upstream Remote:**
   ```bash
   git remote add upstream https://github.com/a37ai/devops-mcp-servers.git
   ```
4. **Create a Feature Branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Style
- Follow the established coding style in the repository
- Include clear and concise comments, especially for complex logic
- Ensure proper type definitions and error handling where applicable
- Keep your code modular and maintainable

### Documentation
- Each new server should have a detailed README.md in its directory
- Document configuration options, setup instructions, and usage examples
- Provide clear examples of how to use the server's features
- Maintain consistency with existing documentation formatting
- Include troubleshooting tips where appropriate

### Testing
- Add appropriate tests for new functionality
- Ensure existing tests pass with your changes
- Add a test script to the 'testing' directory that runs a comprehensive test of all your changes
- Document test procedures in your pull request

### Security
- Follow security best practices
- Validate inputs and handle errors gracefully
- Document any security considerations related to your changes
- Avoid committing sensitive information (API keys, tokens, credentials)

## Contribution Workflow

1. **Sync with Upstream:** Before starting work, ensure your fork is up to date:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Make Your Changes:** Implement your feature or fix on your feature branch

3. **Commit Your Changes:** Make focused, logical commits with clear messages:
   ```bash
   git add .
   git commit -m "feature: Description of changes"
   ```
   
   Use semantic commit messages:
   - `feature:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for test-related changes
   - `refactor:` for code refactoring

4. **Push to Your Fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request:** Navigate to the original repository and open a pull request from your feature branch

## Pull Request Process

- **PR Template:** Fill out the pull request template completely
- **Describe Your Changes:** Clearly explain what your PR accomplishes and why it's valuable
- **Reference Issues:** Link to any related issues using the GitHub issue reference syntax
- **Code Review:** Address any feedback from maintainers promptly
- **Continuous Integration:** Ensure your changes pass any CI checks
- **Approval:** Wait for approval from at least one maintainer before merging

## Community Guidelines

- **Be Respectful:** Treat all contributors with respect and consideration
- **Stay Focused:** Keep discussions relevant to the project and specific features
- **Provide Context:** When reporting bugs or suggesting features, provide as much context as possible
- **Collaborate:** Work together with other contributors to improve the project
- **Ask Questions:** Don't hesitate to seek clarification when needed

Thank you for contributing to Forge's DevOps MCP Servers! Your efforts help build better tools for the entire community.

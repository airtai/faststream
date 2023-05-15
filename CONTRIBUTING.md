# Contributing to fastkafka

First off, thanks for taking the time to contribute! ❤️

All types of contributions are encouraged and valued. See the [Table of Contents](#table-of-contents) for different ways to help and details about how this project handles them. Please make sure to read the relevant section before making your contribution. It will make it a lot easier for us maintainers and smooth out the experience for all involved. The community looks forward to your contributions. 🎉

> And if you like the project, but just don't have time to contribute, that's fine. There are other easy ways to support the project and show your appreciation, which we would also be very happy about:
> - Star the project
> - Tweet about it
> - Refer this project in your project's readme
> - Mention the project at local meetups and tell your friends/colleagues

## Table of Contents

- [I Have a Question](#i-have-a-question)
- [I Want To Contribute](#i-want-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Your First Code Contribution](#your-first-code-contribution)
- [Development](#development)
    - [Prepare the dev environment](#prepare-the-dev-environment)
    - [Way of working](#way-of-working)
    - [Before a PR](#before-a-pr)
- [Join The Project Team](#join-the-project-team)



## I Have a Question

> If you want to ask a question, we assume that you have read the available [Documentation](https://fastkafka.airt.ai/docs).

Before you ask a question, it is best to search for existing [Issues](https://github.com/airtai/fastkafka/issues) that might help you. In case you have found a suitable issue and still need clarification, you can write your question in this issue.

If you then still feel the need to ask a question and need clarification, we recommend the following:

- Contact us on [Discord](https://discord.com/invite/CJWmYpyFbc)
- Open an [Issue](https://github.com/airtai/fastkafka/issues/new)
    - Provide as much context as you can about what you're running into

We will then take care of the issue as soon as possible.

## I Want To Contribute

> ### Legal Notice 
> When contributing to this project, you must agree that you have authored 100% of the content, that you have the necessary rights to the content and that the content you contribute may be provided under the project license.

### Reporting Bugs

#### Before Submitting a Bug Report

A good bug report shouldn't leave others needing to chase you up for more information. Therefore, we ask you to investigate carefully, collect information and describe the issue in detail in your report. Please complete the following steps in advance to help us fix any potential bug as fast as possible.

- Make sure that you are using the latest version.
- Determine if your bug is really a bug and not an error on your side e.g. using incompatible environment components/versions (Make sure that you have read the [documentation](https://fastkafka.airt.ai/docs). If you are looking for support, you might want to check [this section](#i-have-a-question)).
- To see if other users have experienced (and potentially already solved) the same issue you are having, check if there is not already a bug report existing for your bug or error in the [bug tracker](https://github.com/airtai/fastkafkaissues?q=label%3Abug).
- Also make sure to search the internet (including Stack Overflow) to see if users outside of the GitHub community have discussed the issue.
- Collect information about the bug:
  - Stack trace (Traceback)
  - OS, Platform and Version (Windows, Linux, macOS, x86, ARM)
  - Python version
  - Possibly your input and the output
  - Can you reliably reproduce the issue? And can you also reproduce it with older versions?

#### How Do I Submit a Good Bug Report?

We use GitHub issues to track bugs and errors. If you run into an issue with the project:

- Open an [Issue](https://github.com/airtai/fastkafka/issues/new). (Since we can't be sure at this point whether it is a bug or not, we ask you not to talk about a bug yet and not to label the issue.)
- Explain the behavior you would expect and the actual behavior.
- Please provide as much context as possible and describe the *reproduction steps* that someone else can follow to recreate the issue on their own. This usually includes your code. For good bug reports you should isolate the problem and create a reduced test case.
- Provide the information you collected in the previous section.

Once it's filed:

- The project team will label the issue accordingly.
- A team member will try to reproduce the issue with your provided steps. If there are no reproduction steps or no obvious way to reproduce the issue, the team will ask you for those steps and mark the issue as `needs-repro`. Bugs with the `needs-repro` tag will not be addressed until they are reproduced.
- If the team is able to reproduce the issue, it will be marked `needs-fix`, as well as possibly other tags (such as `critical`), and the issue will be left to be implemented.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for fastkafka, **including completely new features and minor improvements to existing functionality**. Following these guidelines will help maintainers and the community to understand your suggestion and find related suggestions.

#### Before Submitting an Enhancement

- Make sure that you are using the latest version.
- Read the [documentation](https://fastkafka.airt.ai/docs) carefully and find out if the functionality is already covered, maybe by an individual configuration.
- Perform a [search](https://github.com/airtai/fastkafka/issues) to see if the enhancement has already been suggested. If it has, add a comment to the existing issue instead of opening a new one.
- Find out whether your idea fits with the scope and aims of the project. It's up to you to make a strong case to convince the project's developers of the merits of this feature. Keep in mind that we want features that will be useful to the majority of our users and not just a small subset. If you're just targeting a minority of users, consider writing an add-on/plugin library.
- If you are not sure or would like to discuiss the enhancement with us directly, you can always contact us on [Discord](https://discord.com/invite/CJWmYpyFbc)

#### How Do I Submit a Good Enhancement Suggestion?

Enhancement suggestions are tracked as [GitHub issues](https://github.com/airtai/fastkafka/issues).

- Use a **clear and descriptive title** for the issue to identify the suggestion.
- Provide a **step-by-step description of the suggested enhancement** in as many details as possible.
- **Describe the current behavior** and **explain which behavior you expected to see instead** and why. At this point you can also tell which alternatives do not work for you.
- **Explain why this enhancement would be useful** to most fastkafka users. You may also want to point out the other projects that solved it better and which could serve as inspiration.

### Your First Code Contribution

A great way to start contributing to FastKafka would be by solving an issue tagged with "good first issue". To find a list of issues that are tagged as "good first issue" and are suitable for newcomers, please visit the following link: [Good first issues](https://github.com/airtai/fastkafka/labels/good%20first%20issue)

These issues are beginner-friendly and provide a great opportunity to get started with contributing to FastKafka. Choose an issue that interests you, follow the contribution process mentioned in [Way of working](#way-of-working) and [Before a PR](#before-a-pr), and help us make FastKafka even better!

If you have any questions or need further assistance, feel free to reach out to us. Happy coding!

## Development

### Prepare the dev environment

To start contributing to fastkafka, you first have to prepare the development environment.

#### Clone the fastkafka repository

To clone the repository, run the following command in the CLI:

```shell
git clone https://github.com/airtai/fastkafka.git
```

#### Optional: create a virtual python environment

To prevent library version clashes with you other projects, it is reccomended that you create a virtual python environment for your fastkafka project by running:

```shell
python3 -m venv fastkafka-env
```

And to activate your virtual environment run:

```shell
source fastkafka-env/bin/activate
```

To learn more about virtual environments, please have a look at [official python documentation](https://docs.python.org/3/library/venv.html#:~:text=A%20virtual%20environment%20is%20created,the%20virtual%20environment%20are%20available.)

#### Install fastkafka

To install fastkafka, navigate to the root directory of the cloned fastkafka project and run:

```shell
pip install fastkafka -e [."dev"]
```

#### Install JRE and Kafka toolkit

To be able to run tests and use all the functionalities of fastkafka, you have to have JRE and Kafka toolkit installed on your machine. To do this, you have two options:

1. Use our `fastkafka testing install-deps` CLI command which will install JRE and Kafka toolkit for you in your .local folder
OR
2. Install JRE and Kafka manually.
   To do this, please refer to [JDK and JRE installation guide](https://docs.oracle.com/javase/9/install/toc.htm) and [Apache Kafka quickstart](https://kafka.apache.org/quickstart)
   
#### Install npm

To be able to run tests you must have npm installed, because of documentation generation. To do this, you have two options:

1. Use our `fastkafka docs install_deps` CLI command which will install npm for you in your .local folder
OR
2. Install npm manually.
   To do this, please refer to [NPM installation guide](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)
   
#### Install docusaurus

To generate the documentation, you need docusaurus. To install it run 'docusaurus/scripts/install_docusaurus_deps.sh' in the root of fastkafka project.

#### Check if everything works

After installing fastkafka and all the necessary dependencies, run `nbdev_test` in the root of fastkafka project. This will take a couple of minutes as it will run all the tests on fastkafka project. If everythng is setup correctly, you will get a "Success." message in your terminal, otherwise please refer to previous steps.

### Way of working

The development of fastkafka is done in Jupyter notebooks. Inside the `nbs` directory you will find all the source code of fastkafka, this is where you will implement your changes.

The testing, cleanup and exporting of the code is being handled by `nbdev`, please, before starting the work on fastkafka, get familiar with it by reading [nbdev documentation](https://nbdev.fast.ai/getting_started.html).

The general philosopy you should follow when writing code for fastkafka is:

- Function should be an atomic functionality, short and concise
   - Good rule of thumb: your function should be 5-10 lines long usually
- If there are more than 2 params, enforce keywording using *
   - E.g.: `def function(param1, *, param2, param3): ...`
- Define typing of arguments and return value
   - If not, mypy tests will fail and a lot of easily avoidable bugs will go undetected
- After the function cell, write test cells using the assert keyword
   - Whenever you implement something you should test that functionality immediately in the cells below 
- Add Google style python docstrings when function is implemented and tested

### Before a PR

After you have implemented your changes you will want to open a pull request to merge those changes into our main branch. To make this as smooth for you and us, please do the following before opening the request (all the commands are to be run in the root of fastkafka project):

1. Format your notebooks: `nbqa black nbs`
2. Close, shutdown, and clean the metadata from your notebooks: `nbdev_clean`
3. Export your code: `nbdev_export`
4. Run the tests: `nbdev_test`
5. Test code typing: `mypy fastkafka`
6. Test code safety with bandit: `bandit -r fastkafka`
7. Test code safety with semgrep: `semgrep --config auto -r fastkafka`

When you have done this, and all the tests are passing, your code should be ready for a merge. Please commit and push your code and open a pull request and assign it to one of the core developers. We will then review your changes and if everythng is in order, we will approve your merge.

## Attribution
This guide is based on the **contributing-gen**. [Make your own](https://github.com/bttger/contributing-gen)!
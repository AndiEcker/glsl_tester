# Using This Package Securely

## Reporting Security Issues

To report a security issue, please email [aecker2@gmail.com](mailto:aecker2@gmail.com).

## Dynamic Execution Of Code Blocks And Evaluable Expressions

The ae package provides powerful functions for to execute code blocks and for to evaluate
expressions, which could be mis-used for to execute inject and execute malicious code
snippets.

These functions are also used for to interpret command line arguments and configuration
file options. Therefore caught has to be taken to prevent that external processes having
write access to your shell scripts and configuration files.

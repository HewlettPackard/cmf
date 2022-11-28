# CMF docs development resources

This directory contains files that are used to create some content for the CMF documentation. This process is not
automated yet. Files in this directory are not supposed to be referenced from documentation pages.

> It also should not be required to automatically redeploy documentation (e.g., with GitHub actions) when documentation
> files change only in this particular directory.

- The [diagrams.drawio](./diagrams.drawio) file is created with [PyCharm](https://www.jetbrains.com/pycharm/)'s 
  [Diagram.NET](https://app.diagrams.net/) plugin. It contains a number of diagrams used in the documentation. Now,
  to update those diagrams, use this file to edit them, them take a screenshot, edit with some editor, and then 
  overwrite corresponding files (e.g., [ML Pipeline Definition](../assets/ml_pipeline_def.png)) used on the main page.


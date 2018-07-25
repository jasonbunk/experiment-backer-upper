# Save your machine learning experiments!

This contains simple utilities to save the state of experiments on startup,
so you can come back to them later, or make comparisons between different experiments.

It recursively zips all code and config files (*.py and *.yaml for example),
and saves a metadata file with the hash of every file,
the git commit hash (the last few lines of "git log"), and the output of "git status".

There is a quick comparator to check the difference between saved experiments.

## No dependencies

It is framework-agnostic, has no dependencies by default, works with Python 2 or 3, and it is easy to add to your experiment launch scripts.

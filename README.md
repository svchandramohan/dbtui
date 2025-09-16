# Welcome to your new dbt project!

## Pull Request Viewer

This repository includes a pull request viewer utility that allows you to see all pull requests for this repository.

### Usage

To view pull requests, run:

```bash
python3 pull_request_viewer.py
```

This will display:
- Current working branch information
- All pull requests (open, closed, and merged)
- Summary statistics
- Direct links to GitHub

### Requirements

Install the required dependencies:

```bash
pip install -r requirements.txt
```

For live GitHub API access (higher rate limits), set the `GITHUB_TOKEN` environment variable:

```bash
export GITHUB_TOKEN=your_github_token_here
python3 pull_request_viewer.py
```

### Using the starter project

Try running the following commands:
- dbt run
- dbt test


### Resources:
- Learn more about dbt [in the docs](https://docs.getdbt.com/docs/introduction)
- Check out [Discourse](https://discourse.getdbt.com/) for commonly asked questions and answers
- Join the [dbt community](https://getdbt.com/community) to learn from other analytics engineers
- Find [dbt events](https://events.getdbt.com) near you
- Check out [the blog](https://blog.getdbt.com/) for the latest news on dbt's development and best practices

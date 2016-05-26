# Clean old coverage report
rm .coverage

# Remove old pyc files
find . -name "*.pyc" -delete

# Run tests with coverage
python -m tests

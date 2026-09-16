### Prisoners Dilemma Simulation 
#### Author: Jon Allen

Simulating Iterative Prisoners Dilemma in Python
Learn more: [Wikipedia](https://en.wikipedia.org/wiki/Prisoner's_dilemma).

### API development

Install the backend and start the development server:

```bash
python -m pip install -e './backend[test]'
uvicorn --app-dir backend app.main:app --reload
```

The API is available at `http://localhost:8000/api/v1`, with interactive
documentation at `http://localhost:8000/docs`.

Run the API tests from the repository root:

```bash
pytest backend/tests
```

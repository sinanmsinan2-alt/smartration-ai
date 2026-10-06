# SmartRation AI — Public Hackathon MVP

This is a working prototype based on the SmartRation AI concept:
**Predict → Prepare → Buy → Risk → Act → Learn**

## Included
- Demand intelligence with contextual signals
- Preparation/BOM calculation
- Procurement recommendation with pack-size constraints
- Expiry / slow-moving risk and money-at-risk
- What-if simulator
- Explainable recommendations
- Human approve/edit/reject workflow
- Actual-vs-predicted learning log
- Demo-ready UI

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Make it public
Recommended: Streamlit Community Cloud.
1. Create a GitHub repository.
2. Upload `app.py` and `requirements.txt`.
3. In Streamlit Community Cloud, deploy the repository and select `app.py`.
4. Share the generated `streamlit.app` URL with judges.

## Important
The prototype uses illustrative demo data and a transparent baseline decision engine. For production, replace the synthetic history with real consumption, inventory, recipes/BOM, supplier lead times, expiry batches and outcome data, then validate forecast error and recommendation quality.

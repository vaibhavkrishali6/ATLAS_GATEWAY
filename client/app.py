import json

import httpx
import streamlit as st


ATLAS_BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT_SECONDS = 10.0

SERVICE_NAMES = {
    "Patients": "patients",
    "Doctors": "doctors",
    "Medicines": "medicines",
}

EXAMPLES = {
    "Patients": {
        "path": "/1",
        "body": {
            "name": "Ava Morgan",
            "age": 29,
            "gender": "female",
            "phone": "555-0199",
            "email": "ava.morgan@example.test",
        },
    },
    "Doctors": {
        "path": "/1",
        "body": {
            "name": "Dr. Sam Lee",
            "specialization": "Cardiology",
            "email": "sam.lee@example.test",
            "phone": "555-0202",
            "availability": True,
        },
    },
    "Medicines": {
        "path": "",
        "body": {
            "name": "Novalune",
            "manufacturer": "Fictional Labs",
            "dosage": "10 mg",
            "stock_quantity": 75,
        },
    },
}


def build_atlas_url(service: str, path: str) -> str:
    normalized_path = path.strip()
    if normalized_path and not normalized_path.startswith("/"):
        normalized_path = f"/{normalized_path}"
    return f"{ATLAS_BASE_URL}/api/{SERVICE_NAMES[service]}{normalized_path}"


st.set_page_config(page_title="Atlas Proxy Client")
st.title("Atlas Proxy Client")
st.caption("This client sends requests only to Atlas at http://localhost:8000.")

service = st.selectbox("Service", SERVICE_NAMES)
method = st.selectbox("HTTP method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
example = EXAMPLES[service]

path = st.text_input(
    "Path",
    placeholder=f"Example: {example['path'] or 'empty for the collection endpoint'}",
)
body_text = st.text_area(
    "JSON request body (optional for GET and DELETE)",
    value=json.dumps(example["body"], indent=2) if method in {"POST", "PUT", "PATCH"} else "",
    height=200,
)

atlas_url = build_atlas_url(service, path)
st.write(f"**Final Atlas URL:** `{atlas_url}`")
st.write(f"**HTTP method:** `{method}`")
st.caption(
    f"For {service}: use GET `{example['path'] or '(empty path)'}`. "
    "Use an empty path for POST collection requests."
)

if st.button("Send Request", type="primary"):
    try:
        request_body = json.loads(body_text) if body_text.strip() else None
    except json.JSONDecodeError as error:
        st.error(f"Invalid JSON request body: {error.msg}")
    else:
        try:
            response = httpx.request(
                method,
                atlas_url,
                json=request_body,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except httpx.TimeoutException:
            st.error("Atlas did not respond within 10 seconds.")
        except httpx.RequestError as error:
            st.error(f"Could not connect to Atlas: {error}")
        else:
            st.write(f"**Response status:** `{response.status_code}`")
            if response.headers:
                st.write("**Response headers:**")
                st.json(dict(response.headers))
            st.write("**Response body:**")
            try:
                st.json(response.json())
            except json.JSONDecodeError:
                st.code(response.text or "<empty response>")

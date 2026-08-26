from locust import HttpUser, task, between

JWT ="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkYWFiNTk2OC00ZDRmLTQzMzgtYTBmYy1iODU3Y2I0MWU2MjAiLCJyb2xlIjoiYWRtaW4iLCJpc3MiOiJhdGxhcy1hdXRoLXNlcnZpY2UiLCJleHAiOjE3ODc3NTMwMzF9.F7rnRXRMvBisRlLOuhiBdDcb5qMDo7jkYkcwpw-uGT_wESZHGK-slgS0x2p9qdhHUQ4aKoirx9CmJArBO1_HSy6qhQD6vH0f0AJodJ-TYhN8Zeq5-wRmMVVVE5PFDWmjPg21Zsf-n-0lsPmq_I07ZOm46qhUiJzBy3TaO6ls2asTHX66NqDNtR1hyQ5mRFrjNRZGpGjqh0HrS1mDP_1wW_7aZjauFOYuM5uSkZ4PrpNLm2Rx33H9gTZhT-HwzK_2qgEJ0zityla50uauwQ4AJ_E-RALqEuOVR9KWkAZ6aEN-kdf_t2JQ0ggLvM97rEDfv7YKG59MUzFZ9dTBcz2p_w"





class AtlasUser(HttpUser):
    wait_time = between(0.1, 0.2)

    @task
    def get_doctor(self):
        self.client.get(
            "/api/doctors/1",
            headers={
                "Authorization": f"Bearer {JWT}",
            },
        )
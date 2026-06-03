class ATSBase:
    name = "base"
    public = False

    def detect(self, url, html):
        raise NotImplementedError

    def fetch_jobs(self, source):
        raise NotImplementedError

    def normalize_job(self, raw, source):
        raise NotImplementedError

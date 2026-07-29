class ImportBatch(BaseModel):

    __tablename__ = "import_batches"

    filename = db.Column(db.String(255))

    commodity = db.Column(db.String(100))

    country = db.Column(db.String(100))

    imported = db.Column(db.Integer, default=0)

    skipped = db.Column(db.Integer, default=0)

    created_by = db.Column(db.String(100))

    notes = db.Column(db.Text)
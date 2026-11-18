import pandas as pd


class CSVService:

    @staticmethod
    def read(file):
        dataframe = pd.read_csv(file, encoding="utf-8-sig")

        # Remove accidental spaces around column names
        dataframe.columns = dataframe.columns.str.strip()

        # Remove a UTF-8 byte-order mark if present
        dataframe.columns = dataframe.columns.str.replace(
            "\ufeff", "", regex=False
        )

        return dataframe
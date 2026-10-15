import sqlite3

import setup_db


def test_setup_database_loads_csv_to_sqlite(tmp_path):
    csv_path = tmp_path / "titanic.csv"
    db_path = tmp_path / "data" / "titanic.sqlite"
    csv_path.write_text(
        "\n".join(
            [
                "PassengerId,Survived,Pclass,Name,Sex,Age,SibSp,Parch,Ticket,Fare,Cabin,Embarked",
                '1,0,3,"Braund, Mr. Owen Harris",male,22,1,0,A/5 21171,7.25,,S',
                '2,1,1,"Cumings, Mrs. John Bradley",female,,1,0,PC 17599,71.2833,C85,',
            ]
        )
    )

    setup_db.setup_database(
        csv_url=csv_path.as_posix(),
        db_path=db_path,
        table_name="passengers",
    )

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("select count(*) from passengers").fetchone()[0]
        columns = [row[1] for row in conn.execute("pragma table_info(passengers)")]
        missing_age_count = conn.execute(
            "select count(*) from passengers where age is null"
        ).fetchone()[0]
        missing_embarked_count = conn.execute(
            "select count(*) from passengers where embarked is null"
        ).fetchone()[0]

    assert rows == 2
    assert "cabin" not in columns
    assert missing_age_count == 0
    assert missing_embarked_count == 0


def test_setup_db_main_returns_one_on_failure(monkeypatch):
    def fail_setup_database(**_kwargs):
        raise RuntimeError("download failed")

    monkeypatch.setattr(setup_db, "setup_database", fail_setup_database)

    assert setup_db.main([]) == 1


def test_parse_args_accepts_cli_overrides():
    args = setup_db.parse_args(
        [
            "--csv-url",
            "local.csv",
            "--db-path",
            "out/custom.db",
            "--table-name",
            "custom_table",
        ]
    )

    assert args.csv_url == "local.csv"
    assert args.db_path.as_posix() == "out/custom.db"
    assert args.table_name == "custom_table"

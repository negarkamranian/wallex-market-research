import pytest
from app.db.postgres import PostgresClient, ResearchRepository
from app.db.models import ResearchRequest, ResearchReport


class TestPostgresPersistence:

    def test_postgres_client_initialization(self, test_db_session):
        client = PostgresClient()
        client.init_db()

        result = test_db_session.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in result.fetchall()]

        assert "research_requests" in tables
        assert "research_reports" in tables

    def test_create_request(self, research_repository, test_db_session):
        request = research_repository.create_request("BTC")

        assert request.id is not None
        assert request.asset == "BTC"
        assert request.created_at is not None

        db_request = test_db_session.query(ResearchRequest).filter(
            ResearchRequest.id == request.id
        ).first()

        assert db_request is not None
        assert db_request.asset == "BTC"

    def test_create_report(self, research_repository, test_db_session):
        request = research_repository.create_request("ETH")

        tools_used = ["get_market_price", "get_internal_sentiment"]
        report_data = {
            "asset": "ETH",
            "risk_level": "Low",
            "sentiment_score": 0.8,
            "tools_used": tools_used,
            "analysis": "Test analysis"
        }

        report = research_repository.create_report(
            request_id=request.id,
            asset="ETH",
            risk_level="Low",
            sentiment_score=0.8,
            tools_used=tools_used,
            report_data=report_data
        )

        assert report.id is not None
        assert report.request_id == request.id
        assert report.asset == "ETH"
        assert report.risk_level == "Low"
        assert report.sentiment_score == "0.8"
        assert report.tools_used == tools_used
        assert report.report_data == report_data
        assert report.created_at is not None

        db_report = test_db_session.query(ResearchReport).filter(
            ResearchReport.id == report.id
        ).first()

        assert db_report is not None
        assert db_report.request_id == request.id

    def test_get_report_by_request_id(self, research_repository, test_db_session):
        request = research_repository.create_request("SOL")

        report_data = {
            "asset": "SOL",
            "risk_level": "Medium",
            "sentiment_score": 0.6,
            "tools_used": ["get_market_price"],
            "analysis": "Solana analysis"
        }

        created_report = research_repository.create_report(
            request_id=request.id,
            asset="SOL",
            risk_level="Medium",
            sentiment_score=0.6,
            tools_used=["get_market_price"],
            report_data=report_data
        )

        retrieved_report = research_repository.get_report_by_request_id(request.id)

        assert retrieved_report is not None
        assert retrieved_report.id == created_report.id
        assert retrieved_report.asset == "SOL"
        assert retrieved_report.risk_level == "Medium"

    def test_get_report_by_nonexistent_request_id(self, research_repository):
        report = research_repository.get_report_by_request_id(99999)

        assert report is None

    def test_multiple_requests_and_reports(self, research_repository, test_db_session):
        assets = ["BTC", "ETH", "SOL"]
        requests = []
        reports = []

        for asset in assets:
            request = research_repository.create_request(asset)
            requests.append(request)

            report = research_repository.create_report(
                request_id=request.id,
                asset=asset,
                risk_level="Low",
                sentiment_score=0.8,
                tools_used=["get_market_price"],
                report_data={"asset": asset, "risk_level": "Low"}
            )
            reports.append(report)

        assert len(requests) == 3
        assert len(reports) == 3

        db_requests = test_db_session.query(ResearchRequest).all()
        db_reports = test_db_session.query(ResearchReport).all()

        assert len(db_requests) >= 3
        assert len(db_reports) >= 3

    def test_database_transaction_rollback_on_error(self, research_repository, test_db_session):
        initial_count = test_db_session.query(ResearchRequest).count()

        try:
            research_repository.create_request("")
        except Exception:
            pass

        final_count = test_db_session.query(ResearchRequest).count()
        assert final_count == initial_count

    def test_report_data_json_storage(self, research_repository, test_db_session):
        request = research_repository.create_request("ADA")

        complex_report_data = {
            "asset": "ADA",
            "risk_level": "High",
            "sentiment_score": 0.3,
            "tools_used": ["get_market_price", "get_internal_sentiment"],
            "market_data": {
                "price": 0.45,
                "volume": 1500000,
                "change_24h": -5.2
            },
            "sentiment_analysis": {
                "social_score": 0.4,
                "news_score": 0.3,
                "overall": 0.35
            },
            "analysis": "Cardano showing bearish signals with declining volume."
        }

        report = research_repository.create_report(
            request_id=request.id,
            asset="ADA",
            risk_level="High",
            sentiment_score=0.3,
            tools_used=["get_market_price", "get_internal_sentiment"],
            report_data=complex_report_data
        )

        retrieved = research_repository.get_report_by_request_id(request.id)

        assert retrieved.report_data == complex_report_data
        assert retrieved.report_data["market_data"]["price"] == 0.45
        assert retrieved.report_data["sentiment_analysis"]["overall"] == 0.35
from nutrifoundation.connectors.ncbi import PMCConnector, parse_pubmed_xml

XML = '<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article><ArticleTitle>Test Trial</ArticleTitle><Journal><Title>Journal X</Title><JournalIssue><PubDate><Year>2024</Year><Month>Sep</Month><Day>3</Day></PubDate></JournalIssue></Journal><AuthorList><Author><ForeName>Ada</ForeName><LastName>Lovelace</LastName></Author></AuthorList><PublicationTypeList><PublicationType>Randomized Controlled Trial</PublicationType></PublicationTypeList><Abstract><AbstractText>Participants were randomized.</AbstractText></Abstract></Article></MedlineCitation><PubmedData><ArticleIdList><ArticleId IdType="doi">10.1/test</ArticleId><ArticleId IdType="pmc">PMC123</ArticleId></ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>'


def test_parse_pubmed_xml():
    article = parse_pubmed_xml(XML)[0]
    assert article.pmid == "123"
    assert article.title == "Test Trial"
    assert article.doi == "10.1/test"
    assert article.pmcid == "PMC123"
    assert article.authors == ("Ada Lovelace",)
    assert article.publication_date.isoformat() == "2024-09-03"
    assert "randomized" in article.abstract


def test_pmc_connector_builds_pmc_request_without_network():
    class Fake(PMCConnector):
        def _get(self, endpoint, params):
            assert endpoint == "efetch.fcgi"
            assert params["db"] == "pmc"
            assert params["id"] == "123"
            return "<article />"

    assert Fake().fetch_full_text_xml("PMC123") == "<article />"

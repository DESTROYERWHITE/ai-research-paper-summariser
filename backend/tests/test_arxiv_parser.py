from app.services.arxiv import parse_arxiv


def test_parse_arxiv_atom_entry() -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
      <entry>
        <id>http://arxiv.org/abs/2401.12345v1</id>
        <updated>2024-01-20T00:00:00Z</updated>
        <published>2024-01-19T00:00:00Z</published>
        <title> Test Paper Title </title>
        <summary> This is an abstract with extra whitespace. </summary>
        <author><name>Ada Lovelace</name></author>
        <author><name>Grace Hopper</name></author>
        <category term="cs.CL" />
        <category term="cs.AI" />
      </entry>
    </feed>"""

    papers = parse_arxiv(xml)

    assert len(papers) == 1
    assert papers[0].id == "2401.12345v1"
    assert papers[0].title == "Test Paper Title"
    assert papers[0].authors == ["Ada Lovelace", "Grace Hopper"]
    assert papers[0].categories == ["cs.CL", "cs.AI"]

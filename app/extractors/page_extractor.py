import hashlib

from bs4 import BeautifulSoup

from app.models.page import Page
from app.models.page_content import PageContent


class PageExtractor:


    def extract(
        self,
        data: dict
    ):

        page = self._extract_page(data)

        content = self._extract_content(data)

        return page, content



    def _extract_page(
        self,
        data: dict
    ):

        ancestors = data.get(
            "ancestors",
            []
        )

        parent_id = None

        if ancestors:
            parent_id = ancestors[-1].get(
                "id"
            )


        history = data.get(
            "history",
            {}
        )


        version_info = data.get(
            "version",
            {}
        )


        created_by = (
            history
            .get("createdBy", {})
            .get("displayName")
        )


        created_date = history.get(
            "createdDate"
        )


        updated_by = (
            version_info
            .get("by", {})
            .get("displayName")
        )


        updated_date = version_info.get(
            "when"
        )


        version = version_info.get(
            "number"
        )


        links = data.get(
            "_links",
            {}
        )


        base_url = links.get(
            "base",
            ""
        )

        web_ui = links.get(
            "webui",
            ""
        )


        url = (
            base_url + web_ui
            if web_ui
            else None
        )


        return Page(

            id=str(
                data["id"]
            ),

            title=data.get(
                "title"
            ),

            space="DPCC",

            url=url,

            parent_id=parent_id,

            status=data.get(
                "status"
            ),

            version=version,

            created_by=created_by,

            created_date=created_date,

            updated_by=updated_by,

            updated_date=updated_date

        )



    def _extract_content(
        self,
        data: dict
    ):

        html = (
            data
            .get("body", {})
            .get("storage", {})
            .get("value", "")
        )


        soup = BeautifulSoup(
            html,
            "html.parser"
        )


        text = soup.get_text(
            separator="\n"
        )

        headings = self._extract_headings(
            soup
        )

        tables = self._extract_tables(
            soup
        )

        code_blocks = self._extract_code_blocks(
            soup
        )

        links = self._extract_links(
            soup
        )

        macros = self._extract_macros(
            soup
        )


        content_hash = hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()


        return PageContent(

            page_id=str(
                data["id"]
            ),

            raw_html=html,

            plain_text=text.strip(),

            headings=headings,

            tables=tables,

            code_blocks=code_blocks,

            links=links,

            macros=macros,

            content_hash=content_hash

        )

    def _extract_tables(self, soup):

        tables = []


        for table in soup.find_all("table"):

            rows = []


            for tr in table.find_all("tr"):

                cells = [
                    cell.get_text(
                        " ",
                        strip=True
                    )
                    for cell in tr.find_all(
                        ["th", "td"]
                    )
                ]


                if cells:
                    rows.append(cells)


            if not rows:
                continue


            headers = rows[0]


            data_rows = []


            for row in rows[1:]:

                item = {}

                for index, value in enumerate(row):

                    if index < len(headers):

                        item[
                            headers[index]
                        ] = value


                data_rows.append(item)


            tables.append(
                {
                    "headers": headers,

                    "rows": data_rows
                }
            )


        return tables

    def _extract_code_blocks(
        self,
        soup
    ):

        blocks = []


        for macro in soup.find_all(
            "ac:structured-macro"
        ):

            name = macro.get(
                "ac:name"
            )


            if name == "code":

                body = macro.find(
                    "ac:plain-text-body"
                )


                language = None


                parameter = macro.find(
                    "ac:parameter"
                )


                if parameter:

                    language = (
                        parameter
                        .get_text(
                            strip=True
                        )
                    )


                if body:

                    blocks.append(
                        {
                            "language": language,

                            "content":
                            body.get_text()
                        }
                    )


        return blocks

    def _extract_headings(self, soup):

        headings = []

        for tag in soup.find_all(
            ["h1", "h2", "h3", "h4"]
        ):

            text = tag.get_text(
                " ",
                strip=True
            )

            if text:
                headings.append(text)

        return headings

    def _extract_links(self, soup):

        links = []

        for link in soup.find_all("a"):

            href = link.get(
                "href"
            )

            text = link.get_text(
                " ",
                strip=True
            )

            if href:

                links.append(
                    {
                        "text": text,
                        "url": href
                    }
                )

        return links

    def _extract_macros(self, soup):

        macros = []

        for macro in soup.find_all(
            "ac:structured-macro"
        ):

            name = macro.get(
                "ac:name"
            )

            if name:

                macros.append(
                    {
                        "type": name,
                        "content":
                            macro.get_text(
                                " ",
                                strip=True
                            )
                    }
                )

        return macros
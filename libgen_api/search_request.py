import requests
from bs4 import BeautifulSoup
import logging


# WHY
# The SearchRequest module contains all the internal logic for the library.
#
# This encapsulates the logic,
# ensuring users can work at a higher level of abstraction.

# USAGE
# req = search_request.SearchRequest("[QUERY]", search_type="[title]")

class SearchRequest:

    nonfiction_col_names = [
        "ID",
        "Author",
        "Title",
        "Publisher",
        "Year",
        "Pages",
        "Language",
        "Size",
        "Extension",
        "Mirror_1",
        "Mirror_2",
        "Mirror_3",
        "Mirror_4",
        "Mirror_5",
        "Edit",
    ]

    fiction_col_names = [
        "Author",
        "Series",
        "Title",
        "Language",
        "File",
        "Mirrors",
        " "
    ]

    def __init__(self, query, search_type="title", search_category="fiction", search_language="English"):
        self.query = query
        self.search_type = search_type
        self.search_category = search_category
        self.search_language = search_language

        if len(self.query) < 3:
            raise Exception("Query is too short")

    def strip_i_tag_from_soup(self, soup):
        subheadings = soup.find_all("i")
        for subheading in subheadings:
            subheading.decompose()

    def get_search_page(self):
        query_parsed = self.check_category()
        if self.search_type.lower() == "title":
            if self.search_category.lower() == "fiction":
                search_url = (
                    f"https://libgen.is/fiction/?q={query_parsed}&criteria=title&language={self.search_language.capitalize()}"
                )
                print(search_url)
            elif self.search_category.lower() == "nonfiction":
                search_url = (
                    f"https://libgen.is/search.php?req={query_parsed}&column=title&language={self.search_language.capitalize()}"
                )
        elif self.search_type.lower() == "author":
            if self.search_category.lower() == "fiction":
                search_url = (
                    f"https://libgen.is/fiction/?q={query_parsed}&criteria=authors&language={self.search_language.capitalize()}"
                )
            search_url = (
                f"https://libgen.is/search.php?req={query_parsed}&column=author&language={self.search_language.capitalize()}"
            )
        search_page = requests.get(search_url)
        return search_page
    
    def check_category(self):
        if self.search_category == "fiction":
            return "+".join(self.query.split(" "))
        else:
            return "%20".join(self.query.split(" "))

    def aggregate_request_data(self):
        search_page = self.get_search_page()
        soup = BeautifulSoup(search_page.text, "lxml")
        self.strip_i_tag_from_soup(soup)

        # Libgen results contain 3 tables
        # Table2: Table of data to scrape.
        if self.search_category == "fiction":
            information_table = soup.find_all("table")[0]
        else:
            information_table = soup.find_all("table")[2]

        # Determines whether the link url (for the mirror)
        # or link text (for the title) should be preserved.
        # Both the book title and mirror links have a "title" attribute,
        # but only the mirror links have it filled.(title vs title="libgen.io")
        # raw_data = [
        #     [
        #         td.a["href"]
        #         if td.find("a")
        #         and td.find("a").has_attr("title")
        #         and td.find("a")["title"] != ""
        #         else "".join(td.stripped_strings)
        #         for td in row.find_all("td")
        #     ]
        #     for row in information_table.find_all("tr")[
        #         1:
        #     ]  # Skip row 0 as it is the headings row
        # ]

        headerRow = information_table.find("tr")
        columnCount = len(headerRow.find_all(['th', 'td']))
        print(columnCount)

        raw_data = [
            [
                [a["href"] for a in td.find_all("a")] if index == (columnCount - 1) else (
                    td.find("a").text if td.find("a") else "".join(td.stripped_strings)
                )
                for index, td in enumerate(row.find_all("td"))
            ]
            for row in information_table.find_all("tr")[1:]
        ]

        if self.search_category == "fiction":
            output_data = [dict(zip(self.fiction_col_names, row)) for row in raw_data]
        else:
            output_data = [dict(zip(self.nonfiction_col_names, row)) for row in raw_data]
        return output_data

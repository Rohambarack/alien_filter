# /// script
# requires-python = "==3.12"
# dependencies = [
#     "datasets>=3.5.0",
#     "plotnine==0.15.3",
# ]
# ///


import os
from datasets import Dataset, concatenate_datasets, load_dataset
import pandas as pd
from plotnine import *

#if less than 10 tokens on a page empty = 1
def e_page(page):
    if page["page_text_n_tokens"] < 10:
        empty = 1 
    else:
        empty = 0
    page.update({"empty_page":empty})
    return page
#make large numbers human readable
def human_readable(x:int) -> str:
    val_list = [1e3,1e6,1e9,1e12,1e15]
    fix_list = ["K","M","B","T"," "]
    
    for idx_val, i_val in enumerate(val_list):
        if x // i_val == 0:
            x = f"{round(x/val_list[idx_val-1],2)}{fix_list[idx_val-1]}"
            break
    return x
# ~number of confirmed danish words 
def found_a_tokens(page):
    n_found = round(
        page["page_text_a_tokens"]*page["page_text_rel_a_words"]
        )
    page.update({"n_confirmed_token":n_found})
    return page


def main():
    #find most recent version
    all_files = os.listdir(".")
    meta_data_files = [i for i in all_files if "meta_data" in i]
    most_recent_filename = sorted(meta_data_files,reverse=True)[0]
    ds = Dataset.from_json(most_recent_filename)
    ##
    ds = ds.map(e_page, num_proc = 4)
    ds = ds.map(found_a_tokens, num_proc = 4)
    ##
    #create aggregates
    by_page = ds.to_pandas()
    ##
    by_book = by_page.groupby(["file_name","published"]).agg(
        total_pages = ("page_id", "count"),
        total_dict_tokens = ("n_confirmed_token", "sum"),
        total_tokens=("page_text_n_tokens", 'sum'),
        empty_pages =("empty_page", "sum"),
        avg_rel_words=("page_text_rel_words", 'mean'),
        avg_rel_a_words=("page_text_rel_a_words", 'mean')
    ).reset_index()
    by_book["empty_book"] = round(by_book["empty_pages"] / by_book["total_pages"])
    ##
    by_p_agg = by_page.groupby(["published"]).agg(
        avg_rel_words=("page_text_rel_words", 'mean'),
        avg_rel_a_words=("page_text_rel_a_words", 'mean')
    ).reset_index()
    ##
    by_year = by_book.groupby(["published"]).agg(
        total_books = ("file_name", "count"),
        total_dict_tokens = ("total_dict_tokens","sum"),
        total_tokens= ("total_tokens", 'sum'),
        empty_books = ("empty_book","sum")
    ).reset_index()
    #readd cols so the values are not mean(mean(book)), but mean(pages)
    by_year["empty_book_rel"] = by_year["empty_books"] / by_year["total_books"]
    by_year["avg_rel_a_words"] = by_p_agg["avg_rel_a_words"]
    by_year["avg_rel_words"] = by_p_agg["avg_rel_words"]
    by_year["published"] = by_year["published"].transform(lambda x: int(x))
    by_year["cumulative_tokens"] = by_year["total_tokens"].cumsum()
    by_year["cum_dict_tokens"] = by_year["total_dict_tokens"].cumsum()
    by_year["cumulative_books"] = by_year["total_books"].cumsum()
    by_year["cumulative_empty"] = by_year["empty_books"].cumsum()
    #### cumulative tokens by year
    cum_toks_by_year = by_year[["published","cumulative_tokens","cum_dict_tokens"]]
    cum_toks_by_year = pd.melt(
                        cum_toks_by_year,
                        id_vars='published',
                        value_vars=[
                            'cumulative_tokens',
                            "cum_dict_tokens"
                            ]
                            )
    ##plot
    cumulative_plots=(
        ggplot(by_year, aes(x="published", y="total_books"))
        + geom_point()
        + ylab("Books")
        + ggtitle("Yearly")
        + xlab(" ")
        + theme_classic()
    | 
        
        ggplot(by_year, aes(x="published", y="cumulative_books"))
        + geom_point()
        + ggtitle("Cumulative")
        + ylab(" ")
        + xlab(" ")
        + theme_classic()
        
    ) / ( ggplot(by_year, aes(x="published", y="total_tokens"))
        + geom_point()
        + ylab("Tokens")
        + xlab(" ")
        + scale_y_continuous(
                            labels=lambda breaks: [human_readable(s) for s in breaks]
                            )
        + theme_classic()
    | 
        ggplot(by_year, aes(x="published", y="cumulative_tokens"))
        + geom_point()
        + ylab(" ")
        + xlab(" ")
        + scale_y_continuous(
                            labels=lambda breaks: [human_readable(s) for s in breaks]
                            )
        + theme_classic()

    ) / ( ggplot(by_year, aes(x="published", y="empty_books"))
        + geom_point()
        + ylab("Empty Books")
        + xlab(" ")
        + theme_classic()
    | 
        ggplot(by_year, aes(x="published", y="cumulative_empty"))
        + geom_point()
        + ylab(" ")
        + xlab(" ")
        + theme_classic()

    )
    cumulative_plots.save(os.path.join("..","imgs","cumulative_metadata.jpg"))

if __name__ == "__main__":
    main()
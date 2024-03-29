import argparse
from dataclasses import asdict
import json
import os
import streamlit as st

from data_driven_characters.character import get_character_definition
from data_driven_characters.corpus import (
    get_corpus_summaries,
    load_docs,
)

from data_driven_characters.chatbots import (
    SummaryChatBot,
    RetrievalChatBot,
    SummaryRetrievalChatBot,
)
from data_driven_characters.interfaces import CommandLine, Streamlit
from data_driven_characters.chatbots.function_tools import add_balloons

OUTPUT_ROOT = "output"


def create_chatbot(corpus, character_name, chatbot_type, retrieval_docs, summary_type):
    # logging
    corpus_name = os.path.splitext(os.path.basename(corpus))[0]
    output_dir = f"{OUTPUT_ROOT}/{corpus_name}/summarytype_{summary_type}"
    os.makedirs(output_dir, exist_ok=True)
    summaries_dir = f"{output_dir}/summaries"
    character_definitions_dir = f"{output_dir}/character_definitions"
    os.makedirs(character_definitions_dir, exist_ok=True)

    # load docs
    docs = load_docs(corpus_path=corpus, chunk_size=2048, chunk_overlap=64)
    # resume = docs[1]
    # docs = docs[0]

    # generate summaries
    corpus_summaries = get_corpus_summaries(
        docs=docs, summary_type=summary_type, cache_dir=summaries_dir
    )

    # get character definition
    character_definition = get_character_definition(
        name=character_name,
        corpus_summaries=corpus_summaries,
        cache_dir=character_definitions_dir,
    )
    print(json.dumps(asdict(character_definition), indent=4))

    # construct retrieval documents
    if retrieval_docs == "raw":
        documents = [
            doc.page_content
            for doc in load_docs(corpus_path=corpus, chunk_size=256, chunk_overlap=16)
        ]
    elif retrieval_docs == "summarized":
        documents = corpus_summaries
    else:
        raise ValueError(f"Unknown retrieval docs type: {retrieval_docs}")

    # initialize chatbot
    if chatbot_type == "summary":
        chatbot = SummaryChatBot(character_definition=character_definition)
    elif chatbot_type == "retrieval":
        chatbot = RetrievalChatBot(
            character_definition=character_definition,
            documents=documents,
        )
    elif chatbot_type == "summary_retrieval":
        chatbot = SummaryRetrievalChatBot(
            character_definition=character_definition,
            documents=documents,
        )
    else:
        raise ValueError(f"Unknown chatbot type: {chatbot_type}")
    return chatbot


def main():
    #change your character defualts here
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus", type=str, default="data/resume.txt"
    )
    parser.add_argument(
        "--character_name",
        type=str, 
        default="RyanThiago"
    )
    parser.add_argument(
        "--chatbot_type",
        type=str,
        default="retrieval",
        choices=["summary", "retrieval", "summary_retrieval"],
    )
    parser.add_argument(
        "--summary_type",
        type=str,
        default="map_reduce",
        choices=["map_reduce", "refine"],
    )
    parser.add_argument(
        "--retrieval_docs",
        type=str,
        default="raw",
        choices=["raw", "summarized"],
    )
    parser.add_argument(
        "--interface", type=str, default="streamlit", choices=["cli", "streamlit"]
    )
    args = parser.parse_args()

    if args.interface == "cli":
        chatbot = create_chatbot(
            args.corpus,
            args.character_name,
            args.chatbot_type,
            args.retrieval_docs,
            args.summary_type,
        )
        app = CommandLine(chatbot=chatbot)
    elif args.interface == "streamlit":
        chatbot = st.cache_resource(create_chatbot)(
            args.corpus,
            args.character_name,
            args.chatbot_type,
            args.retrieval_docs,
            args.summary_type,
        )
        # the streamlit UI begins here and finishes in interfaces/streamlit_ui.py
        st.title("<>{}</> GPT".format(args.character_name))
        st.write("An AI thats trained to be like {}! Ask {} anything about their resume, work experince and personal life.".format(args.character_name, args.character_name))
        with st.expander("details"):
            st.markdown("""*This AI assistant references details to simulate conversation. It's not a real person,
                         so some info might be wrong. AI can sometimes generate unexpected responses. Use it for fun.*""")
            st.markdown(f"**chatbot type**: *{args.chatbot_type}*")
            st.markdown(f"youtube video: https://youtu.be/50Z0RKRtI6M?si=LV1vlZ_lFcpQIIAC")
            if st.button('Chaos Mode'):
                add_balloons()
            
            app = Streamlit(chatbot=chatbot)
    else:
        raise ValueError(f"Unknown interface: {args.interface}")
    st.divider()
  
    app.run()


if __name__ == "__main__":
    main()

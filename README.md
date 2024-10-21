Main contributions of this project:

(1) Traditional RAG (Retrieval-Augmented Generation) technologies are typically implemented using vector databases. Unlike the traditional approach, this project employs a knowledge graph to provide the large language model with more accurate external information.

(2) This project constructed a knowledge graph in the medical field, and optimized the entity information in the knowledge graph dataset using a large language model, making the constructed knowledge graph more accurate and scientific.

(3) The project created an entity recognition dataset (NER) through rule-based matching. Thanks to the optimization of entity names in (2), our model can easily achieve outstanding performance on the constructed dataset.

(4) For the entity recognition task, the project proposed and implemented three data augmentation strategies: entity replacement, entity masking, and entity concatenation, which improved the performance of the RoBERTa model. On the test set, these augmentation strategies raised the RoBERTa model’s F1 score from 96.77% to 97.40%.

(5) To avoid the labor costs associated with data annotation, the project directly designed prompts, combined with contextual learning and chain-of-thought techniques, to use a large language model for intent recognition of user questions. This method reduces manual costs while ensuring accuracy in the intent recognition process.

(6) The project used the Streamlit framework to deploy the aforementioned models, achieving a high level of encapsulation. Our interface includes various features such as registration and login, selection of large language models, and the creation of multiple chat windows.

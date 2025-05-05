from utils.retriever import inventory_qa_chain

while True:
    question  = input("You: ")
    if question.lower() == "exit":
        print("Exiting...")
        break
    response = inventory_qa_chain.invoke(question)
    print(f"Inventory AI: {response}")
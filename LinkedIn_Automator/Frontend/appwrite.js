import { Client, Account } from "appwrite";

const client = new Client()
  .setEndpoint("https://cloud.appwrite.io/v1")
  .setProject("67aadcbc003bd79f7355");

const account = new Account(client);

export { account, client };

const AGNV_CONTRACT = "0x8515Be9209E1e4e2D13ed54f2d6F782Ac924fb85";

const AGNV_ABI = [
  "function name() view returns (string)",
  "function symbol() view returns (string)",
  "function decimals() view returns (uint8)",
  "function balanceOf(address) view returns (uint256)"
];

let provider = null;
let signer = null;
let walletAddress = null;
let agnvContract = null;

async function connectWallet() {

  if (!window.ethereum) {
    alert(
      "Aucun wallet compatible détecté. Ouvre AgriNova depuis un navigateur compatible wallet."
    );
    return;
  }

  try {

    provider = new ethers.BrowserProvider(window.ethereum);

    const network = await provider.getNetwork();

    if (network.chainId !== 97n) {

      try {

        await window.ethereum.request({
          method: "wallet_switchEthereumChain",
          params: [
            { chainId: "0x61" }
          ]
        });

      } catch (switchError) {

        if (switchError.code === 4902) {

          await window.ethereum.request({
            method: "wallet_addEthereumChain",
            params: [{
              chainId: "0x61",
              chainName: "BSC Testnet",
              nativeCurrency: {
                name: "tBNB",
                symbol: "tBNB",
                decimals: 18
              },
              rpcUrls: [
                "https://data-seed-prebsc-1-s1.bnbchain.org:8545"
              ],
              blockExplorerUrls: [
                "https://testnet.bscscan.com/"
              ]
            }]
          });

        } else {

          throw switchError;

        }
      }

      provider = new ethers.BrowserProvider(window.ethereum);

    }

    const accounts =
      await provider.send("eth_requestAccounts", []);

    walletAddress = accounts[0];

    signer = await provider.getSigner();

    agnvContract =
      new ethers.Contract(
        AGNV_CONTRACT,
        AGNV_ABI,
        provider
      );

    const [
      name,
      symbol,
      decimals,
      balance
    ] = await Promise.all([

      agnvContract.name(),

      agnvContract.symbol(),

      agnvContract.decimals(),

      agnvContract.balanceOf(walletAddress)

    ]);

    const formattedBalance =
      ethers.formatUnits(balance, decimals);

    document.getElementById("walletStatus")
      .textContent = "🟢 Wallet connecté";

    document.getElementById("walletAddress")
      .textContent =
        walletAddress.slice(0, 6) +
        "..." +
        walletAddress.slice(-4);

    document.getElementById("walletNetwork")
      .textContent =
        "BSC Testnet — Chain ID 97";

    document.getElementById("agnvBalance")
      .textContent =
        `${formattedBalance} ${symbol}`;

    document.getElementById("agnvName")
      .textContent = name;

    document.getElementById("connectWalletBtn")
      .textContent = "Wallet connecté";

    console.log("========================================");
    console.log("🌱 AGRINOVA WALLET CONNECT");
    console.log("========================================");
    console.log("Adresse :", walletAddress);
    console.log("Réseau  : BSC Testnet");
    console.log("Chain ID: 97");
    console.log("Token   :", name);
    console.log("Symbole :", symbol);
    console.log("Décimales :", decimals);
    console.log("Solde AGNV :", formattedBalance);
    console.log("========================================");

  } catch (error) {

    console.error("❌ Wallet error:", error);

    alert(
      "Connexion impossible : " +
      (error.shortMessage || error.message)
    );

  }

}

async function disconnectDisplay() {

  walletAddress = null;
  signer = null;
  provider = null;
  agnvContract = null;

  document.getElementById("walletStatus")
    .textContent = "⚪ Wallet non connecté";

  document.getElementById("walletAddress")
    .textContent = "—";

  document.getElementById("walletNetwork")
    .textContent = "—";

  document.getElementById("agnvBalance")
    .textContent = "—";

}

if (window.ethereum) {

  window.ethereum.on("accountsChanged", () => {
    location.reload();
  });

  window.ethereum.on("chainChanged", () => {
    location.reload();
  });

}

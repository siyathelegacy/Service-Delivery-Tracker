// scripts/deploy.js
async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);

  const Security = await ethers.getContractFactory("ServiceDeliveryTrackerSecurity");
  const security = await Security.deploy("0x0000000000000000000000000000000000000000");
  await security.deployed();
  console.log("ServiceDeliveryTrackerSecurity deployed to:", security.address); 
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

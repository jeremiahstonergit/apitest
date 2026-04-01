# API Inventory (extracted from OpenRPC in apidoc.sweb.ru)

Total methods: **276**

## domains/openrpc.bonus.json (3 methods)
Servers: https://api.sweb.ru/domains/bonus

- `buy`
- `getList`
- `index`

## domains/openrpc.persons.json (4 methods)
Servers: https://api.sweb.ru/domains/persons

- `createFizIp`
- `createJur`
- `getinfo`
- `index`

## monitoring/openrpc.checks.json (16 methods)
Servers: https://api.sweb.ru/monitoring/checks

- `activate`
- `activateList`
- `create`
- `deactivate`
- `deactivateList`
- `edit`
- `getFullCheckInfo`
- `getInfo`
- `getIntervals`
- `getKeywordModes`
- `getPorts`
- `getTypes`
- `history`
- `index`
- `remove`
- `removeList`

## monitoring/openrpc.monitoring.json (4 methods)
Servers: https://api.sweb.ru/monitoring

- `change`
- `disable`
- `enable`
- `plans`

## monitoring/openrpc.monitoringcontacts.json (15 methods)
Servers: https://api.sweb.ru/monitoring/contacts

- `addContact`
- `addEmail`
- `addPhone`
- `addTelegram`
- `deleteContact`
- `deleteContacts`
- `editContact`
- `editEmail`
- `editPhone`
- `editTelegram`
- `getAllContacts`
- `index`
- `isVerified`
- `requestTelegramVerifyCode`
- `verifyContact`

## openrpc.dns.json (6 methods)
Servers: https://api.sweb.ru/domains/dns

- `editMx`
- `editNS`
- `editSrv`
- `editTxt`
- `getFile`
- `info`

## openrpc.domains.json (21 methods)
Servers: https://api.sweb.ru/domains

- `changeProlong`
- `changeProlongList`
- `createSubdomain`
- `getAvailablePackages`
- `getDomainInfo`
- `getRedirectVh`
- `getSubdomains`
- `index`
- `move`
- `moveList`
- `priceForRegistration`
- `priceForTrasfer`
- `prolong`
- `prolongList`
- `reg`
- `regAvailable`
- `regList`
- `remove`
- `removeList`
- `removeSubdomain`
- `setRedirectVh`

## openrpc.pay.json (10 methods)
Servers: https://api.sweb.ru/pay

- `changeDeferment`
- `getActiveReserves`
- `getBalance`
- `getPayRecommendations`
- `getRecommendationTotalCost`
- `getRemainsDate`
- `getRemainsDays`
- `getUpcomingPaymentsVh`
- `index`
- `isAutopaymentEnable`

## openrpc.sites.json (8 methods)
Servers: https://api.sweb.ru/sites

- `add`
- `changeBackEnd`
- `changeDomainSite`
- `del`
- `edit`
- `getBackEndsList`
- `getSiteInfo`
- `index`

## openrpc.tariff.json (2 methods)
Servers: https://api.sweb.ru/tariff

- `index`
- `serverInfo`

## openrpc.vps.json (20 methods)
Servers: https://api.sweb.ru/vps

- `changePlan`
- `copy`
- `create`
- `createEnable`
- `createFirst`
- `getAvailableConfig`
- `getConstructorPlanId`
- `getCurrentAction`
- `getFirstOrderInfo`
- `index`
- `isRunning`
- `load`
- `logs`
- `powerOff`
- `powerOn`
- `reboot`
- `reinstallOs`
- `remove`
- `removeFirst`
- `rename`

## vh/openrpc.backup.json (9 methods)
Servers: https://api.sweb.ru/vh/backup

- `downloadFile`
- `getList`
- `getListFiles`
- `getListMysql`
- `makeAccountCopy`
- `receiveFiles`
- `receiveMysql`
- `restoreFiles`
- `restoreMysql`

## vh/openrpc.cron.json (4 methods)
Servers: https://api.sweb.ru/vh/cron

- `addTask`
- `editTask`
- `getTasks`
- `removeTask`

## vh/openrpc.ddg.json (7 methods)
Servers: https://api.sweb.ru/vh/ddg

- `countAllDomains`
- `disable`
- `enable`
- `enableInfo`
- `getPrice`
- `index`
- `priceWidget`

## vh/openrpc.hosting.json (14 methods)
Servers: https://api.sweb.ru/vh/hosting

- `databaseEditComment`
- `databaseGetList`
- `databaseMysqlAccessCreate`
- `databaseMysqlAccessDelete`
- `databaseMysqlAccessList`
- `databaseMysqlChangePass`
- `databaseMysqlCreate`
- `databaseMysqlDelete`
- `databaseMysqlImport`
- `databaseMysqlMakeCopy`
- `databasePgsqlChangePass`
- `databasePgsqlCreate`
- `databasePgsqlDelete`
- `getPmaUser`

## vh/openrpc.load.json (2 methods)
Servers: https://api.sweb.ru/vh/load

- `getLoadTable`
- `index`

## vh/openrpc.mail.json (37 methods)
Servers: https://api.sweb.ru/vh/mail

- `addDeliveryAddress`
- `addForwardingEmail`
- `addToBlacklist`
- `addToWhitelist`
- `changeAutoDiscover`
- `changeAutoreply`
- `changeDeletingAfterForwarding`
- `changeDomainSpf`
- `changeMailboxPassword`
- `changeMailboxSpf`
- `changeMailsCollector`
- `changeSenderVerify`
- `confirmMailsCollectorEmail`
- `createMbox`
- `deleteMails`
- `disableDkim`
- `dropDeliveryAddress`
- `dropFromBlacklist`
- `dropFromWhitelist`
- `dropMbox`
- `enableDkim`
- `getAutoreply`
- `getBlacklist`
- `getDeliveryAddressesList`
- `getDeliveryInfo`
- `getDomainsList`
- `getForwardingEmailsList`
- `getMailQuota`
- `getMailboxesList`
- `getMailsCollector`
- `getWhitelist`
- `isEnabledDeletingAfterForwarding`
- `removeForwardingEmail`
- `removeMailsCollector`
- `sendRequisitesToEmail`
- `updateAntispamState`
- `updateComment`

## vh/openrpc.partnerprogram.json (20 methods)
Servers: https://api.sweb.ru/vh/partnerProgram

- `checkLogin`
- `createOrderVh`
- `createOrderVip`
- `createOrderVps`
- `fillPartnerRequisites`
- `getAdvertMaterials`
- `getLinkStatistics`
- `getPartnerClientCard`
- `getPartnerClientLogEvents`
- `getPartnerClientLogFinance`
- `getPartnerClientsList`
- `getRequisitesWithdrawal`
- `getStatistic`
- `getTypesAdvertMaterials`
- `savePartnerClientComment`
- `sendWithdrawalOrder`
- `standardPlans`
- `startPartnership`
- `vipPlans`
- `vpsOsConfig`

## vh/openrpc.referralprogram.json (4 methods)
Servers: https://api.sweb.ru/vh/referralProgram

- `addReferralSite`
- `confirmReferralSite`
- `index`
- `removeReferralSite`

## vh/openrpc.ssl.json (8 methods)
Servers: https://api.sweb.ru/vh/ssl

- `download`
- `editAutoprolong`
- `getOrderList`
- `getProlongInfo`
- `index`
- `installLetsEncrypt`
- `prolongCertificate`
- `removeCertificate`

## vh/openrpc.utils.json (2 methods)
Servers: https://api.sweb.ru/vh/utils

- `sshOff`
- `sshOn`

## vh/utils/openrpc.diskusage.json (5 methods)
Servers: https://api.sweb.ru/vh/utils/diskUsage

- `changeEmail`
- `getEmail`
- `getTasksInfo`
- `index`
- `startTask`

## vps/openrpc.backup.json (9 methods)
Servers: https://api.sweb.ru/vps/backup

- `attach`
- `create`
- `detach`
- `getSettings`
- `index`
- `remove`
- `restore`
- `saveSettings`
- `updateIndex`

## vps/openrpc.balancer.json (6 methods)
Servers: https://api.sweb.ru/balancer

- `create`
- `edit`
- `getAvailableConfig`
- `index`
- `isCreateEnable`
- `remove`

## vps/openrpc.dbaas.json (11 methods)
Servers: https://api.sweb.ru/dbaas

- `createInstance`
- `deleteDatabase`
- `editInstance`
- `getAvailableConfig`
- `getConstructorPlanId`
- `getFirstOrderInfo`
- `index`
- `removeFirst`
- `removeInstance`
- `setUpgradeAgree`
- `validateUsers`

## vps/openrpc.ip.json (2 methods)
Servers: https://api.sweb.ru/vps/ip

- `addLocal`
- `removeLocal`

## vps/openrpc.protected-ip.json (14 methods)
Servers: https://api.sweb.ru/vps/ip

- `add`
- `addLocal`
- `addProtected`
- `editPtr`
- `getAllIpList`
- `getOrderInfo`
- `getPtr`
- `index`
- `move`
- `moveProtected`
- `remove`
- `removeLocal`
- `removeProtected`
- `updateProtected`

## vps/openrpc.remoteBackup.json (6 methods)
Servers: https://api.sweb.ru/vps/remoteBackup

- `create`
- `editComment`
- `index`
- `remove`
- `restore`
- `restoreInto`

## vps/openrpc.ssl.json (7 methods)
Servers: https://api.sweb.ru/vps/ssl

- `download`
- `editAutoprolong`
- `getOrderList`
- `getProlongInfo`
- `index`
- `orderSubmit`
- `removeCertificate`

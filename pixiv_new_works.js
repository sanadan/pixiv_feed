#!/usr/bin/env node

const PixivApi = require('pixiv-api-client')
const pixiv = new PixivApi()
const argv = process.argv

if (argv.length < 4) {
  console.log('{"has_error":true,"errors":{"system":{"message":"-1:引数が足りません","code":-1}}}')
  process.exit(1)
}

pixiv.login(process.argv[2], process.argv[3]).then(() => {
  return pixiv.illustFollow().then(json => {
    console.log(JSON.stringify(json))
  })
}).catch(reason => {
  console.log(JSON.stringify(reason))
})


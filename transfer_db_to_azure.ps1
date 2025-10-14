az login
$ctx =New-AzStorageContext -StorageAccountName "mystracc125"

$DFBlob = @{
   File             = "D:\KnesseetNLP\filtered_utterances_data.pkl"
   Container        = 'knessetdata'
   Blob             = "utterances_data.pkl"
   Context          = $ctx
   StandardBlobTier = 'Cold'
 }
 $DBBlob = @{
   File             = "D:\KnesseetNLP\committie_index"
   Container        = 'knessetdata'
   Blob             = "committie_index"
   Context          = $ctx
   StandardBlobTier = 'Cold'
 }
 Set-AzStorageBlobContent @DFBlob
 Set-AzStorageBlobContent @DBBlob

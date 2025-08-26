export  function resolveServerURI(address:string){
    const isProduction = process.env.NODE_ENV === 'production';
    if (isProduction) {
        return address;
    } else {
        return `http://localhost:3000${address}`;
    }
}
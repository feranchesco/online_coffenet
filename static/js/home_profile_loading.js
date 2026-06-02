
let profileBtn = document.getElementById("profileBtn");
    const homePage = document.getElementById("homePage");
    let homeBtn = document.getElementById("homeBtn");
    let userPanelBtn = document.getElementById("userPanBtn");
    let profilePage = document.getElementById("profilePage");
    let backBtn = document.querySelector(".back-btn");
    function showHomePage() {
        history.replaceState({}, document.title, window.location.pathname);
        if(profilePage){
            profilePage.style.display = "none";
        }
        homePage.style.display = "block";
    }
    function showProfilePage(){
        if(profileBtn){
            window.location.hash = "profile";
            homePage.style.display = "none";
            profilePage.style.display = "block";
        }
    }
    function handleHashChange(){
        let hash = window.location.hash.substring(1);
        if (profilePage && hash==="profile"){
            showProfilePage();
        }else if(homePage){
            showHomePage();
        }
    }
    if(profileBtn){
    profileBtn.addEventListener("click", showProfilePage);
    }
    if (backBtn){
        backBtn.addEventListener("click", showHomePage)
    }
    if(homeBtn && homePage){
        homeBtn.addEventListener("click",showHomePage);
    }else{
        homeBtn?.addEventListener("click", () => {
            window.location.href="/";
        })
    }
    if(userPanelBtn && homePage){
        userPanelBtn.addEventListener("click",showProfilePage);
    }else{
        userPanelBtn?.addEventListener("click",() =>{
            window.location.href = "/#profile";
        });
    }

    window.addEventListener("hashchange",handleHashChange);
    window.addEventListener("DOMContentLoaded",handleHashChange);

if (window.history.replaceState)
{
  window.history.replaceState( null, null, window.location.href);
}

function validateForm()
{
    var name = document.forms["form"]["username"].value;
    var text = document.forms["form"]["tweet"].value;
    reg_name = new RegExp("\\s+");

    if (name.trim()!=null && name.trim()!="" &&  text.trim()!=null && text.trim()!="" && reg_name.test(name) === false)
    {
        document.getElementById("submit").disabled = false;
    }
    else
    {
        document.getElementById("submit").disabled = true;
        document.getElementById("post").disabled = true;
    }
};





